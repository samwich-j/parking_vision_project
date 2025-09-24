#!/usr/bin/env python3
"""
Main Parking Lot Monitoring System
Combines car detection with parking spot analysis to track occupancy in real-time.
"""

import cv2
import numpy as np
import json
import argparse
import os
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

# Import our custom modules
from car_detector import CarDetector


class ParkingMonitor:
    def __init__(self, video_path: str, spots_config: str):
        """
        Initialize parking monitor

        Args:
            video_path: Path to parking lot video
            spots_config: Path to parking spots configuration JSON
        """
        self.video_path = video_path
        self.spots_config = spots_config
        self.video = None
        self.spots = []
        self.car_detector = CarDetector()
        self.frame_count = 0
        self.total_spots = 0
        self.occupied_spots = 0

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('output/logs/parking_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Tracking data
        self.occupancy_history = []
        self.last_update_time = time.time()

        # Colors for visualization
        self.colors = {
            'free': (0, 255, 0),         # Green for free spots
            'occupied': (0, 0, 255),     # Red for occupied spots
            'electric_free': (0, 255, 255),    # Yellow for free electric
            'electric_occupied': (0, 100, 255),  # Orange for occupied electric
            'reserved': (128, 128, 128),  # Gray for reserved spots
            'cone_detected': (255, 0, 255)  # Magenta for cone detection
        }

    def load_spots_config(self) -> bool:
        """
        Load parking spots configuration

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.spots_config, 'r') as f:
                config = json.load(f)

            self.spots = config['spots']
            self.total_spots = len(self.spots)

            # Initialize occupancy status
            for spot in self.spots:
                spot['occupied'] = False
                spot['last_detection_time'] = 0
                spot['confidence'] = 0.0

            self.logger.info(f"Loaded {len(self.spots)} parking spots from {self.spots_config}")

            # Log spot types
            spot_types = {}
            for spot in self.spots:
                spot_type = spot.get('type', 'normal')
                spot_types[spot_type] = spot_types.get(spot_type, 0) + 1

            for spot_type, count in spot_types.items():
                self.logger.info(f"  {spot_type.title()}: {count} spots")

            return True

        except Exception as e:
            self.logger.error(f"Error loading spots config: {str(e)}")
            return False

    def load_video(self) -> bool:
        """
        Load video file

        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.video_path):
            self.logger.error(f"Video file not found: {self.video_path}")
            return False

        self.video = cv2.VideoCapture(self.video_path)
        if not self.video.isOpened():
            self.logger.error(f"Could not open video: {self.video_path}")
            return False

        # Get video properties
        fps = self.video.get(cv2.CAP_PROP_FPS)
        frame_count = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.logger.info(f"Video loaded: {width}x{height} @ {fps:.1f}fps, {frame_count} frames")
        return True

    def point_in_polygon(self, point: Tuple[int, int], polygon: List[Tuple[int, int]]) -> bool:
        """
        Check if a point is inside a polygon using ray casting algorithm

        Args:
            point: (x, y) coordinates of the point
            polygon: List of (x, y) coordinates defining the polygon

        Returns:
            True if point is inside polygon, False otherwise
        """
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def detect_orange_cones(self, frame: np.ndarray) -> List[Tuple[int, int]]:
        """
        Detect orange cones in the frame using color detection

        Args:
            frame: Input frame

        Returns:
            List of (x, y) coordinates of detected cones
        """
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define range for orange color
        lower_orange = np.array([10, 100, 100])
        upper_orange = np.array([25, 255, 255])

        # Create mask for orange pixels
        mask = cv2.inRange(hsv, lower_orange, upper_orange)

        # Apply morphological operations to clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        cone_centers = []
        for contour in contours:
            area = cv2.contourArea(contour)
            # Filter by area (cones should be medium-sized objects)
            if 200 < area < 2000:
                # Calculate center of contour
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    cone_centers.append((cx, cy))

        return cone_centers

    def check_spot_occupancy(self, frame: np.ndarray, detections: List[Dict]) -> None:
        """
        Check occupancy status for each parking spot

        Args:
            frame: Current video frame
            detections: List of car detections from car detector
        """
        # Detect orange cones
        orange_cones = self.detect_orange_cones(frame)

        for spot in self.spots:
            spot_polygon = [(p[0], p[1]) for p in spot['points']]
            spot_occupied = False
            max_confidence = 0.0

            # Check for car detections in this spot
            for detection in detections:
                bbox = detection['bbox']
                confidence = detection['confidence']

                # Calculate center of bounding box
                center_x = bbox[0] + bbox[2] // 2
                center_y = bbox[1] + bbox[3] // 2

                # Check if car center is in parking spot
                if self.point_in_polygon((center_x, center_y), spot_polygon):
                    spot_occupied = True
                    max_confidence = max(max_confidence, confidence)

            # Check for orange cones in this spot
            for cone_x, cone_y in orange_cones:
                if self.point_in_polygon((cone_x, cone_y), spot_polygon):
                    spot_occupied = True
                    max_confidence = max(max_confidence, 0.8)  # High confidence for cone detection

            # Update spot status
            spot['occupied'] = spot_occupied
            spot['confidence'] = max_confidence
            if spot_occupied:
                spot['last_detection_time'] = time.time()

        # Calculate total occupancy
        self.occupied_spots = sum(1 for spot in self.spots if spot['occupied'])

    def get_spot_color(self, spot: Dict) -> Tuple[int, int, int]:
        """
        Get color for spot visualization based on type and occupancy

        Args:
            spot: Spot dictionary

        Returns:
            BGR color tuple
        """
        spot_type = spot.get('type', 'normal')
        occupied = spot['occupied']

        if spot_type == 'electric':
            return self.colors['electric_occupied'] if occupied else self.colors['electric_free']
        elif spot_type == 'reserved':
            return self.colors['reserved']
        else:
            return self.colors['occupied'] if occupied else self.colors['free']

    def draw_spots(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw parking spots on frame with occupancy status

        Args:
            frame: Input frame

        Returns:
            Frame with spots drawn
        """
        display_frame = frame.copy()

        for spot in self.spots:
            points = np.array(spot['points'], np.int32)
            color = self.get_spot_color(spot)
            confidence = spot.get('confidence', 0)

            # Draw filled polygon
            overlay = display_frame.copy()
            cv2.fillPoly(overlay, [points], color)
            cv2.addWeighted(display_frame, 0.7, overlay, 0.3, 0, display_frame)

            # Draw outline
            thickness = 3 if spot['occupied'] else 2
            cv2.polylines(display_frame, [points], True, color, thickness)

            # Draw spot ID and info
            center_x = int(np.mean([p[0] for p in spot['points']]))
            center_y = int(np.mean([p[1] for p in spot['points']]))

            # Spot ID
            cv2.putText(display_frame, str(spot['id']), (center_x-10, center_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Confidence (if occupied)
            if spot['occupied'] and confidence > 0:
                cv2.putText(display_frame, f"{confidence:.2f}",
                           (center_x-15, center_y+15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        return display_frame

    def draw_info_panel(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw information panel with statistics

        Args:
            frame: Input frame

        Returns:
            Frame with info panel
        """
        display_frame = frame.copy()
        height, width = display_frame.shape[:2]

        # Create info panel background
        panel_height = 150
        panel_width = 300
        panel_x = width - panel_width - 10
        panel_y = 10

        overlay = display_frame.copy()
        cv2.rectangle(overlay, (panel_x, panel_y),
                     (panel_x + panel_width, panel_y + panel_height),
                     (0, 0, 0), -1)
        cv2.addWeighted(display_frame, 0.7, overlay, 0.3, 0, display_frame)

        # Draw border
        cv2.rectangle(display_frame, (panel_x, panel_y),
                     (panel_x + panel_width, panel_y + panel_height),
                     (255, 255, 255), 2)

        # Add text information
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        color = (255, 255, 255)
        thickness = 2

        y_offset = panel_y + 25
        line_height = 20

        # Title
        cv2.putText(display_frame, "PARKING STATUS",
                   (panel_x + 10, y_offset), font, 0.7, color, thickness)
        y_offset += line_height * 1.5

        # Statistics
        available = self.total_spots - self.occupied_spots
        cv2.putText(display_frame, f"Total Spots: {self.total_spots}",
                   (int(panel_x + 10), int(y_offset)), font, font_scale, color, 1)
        y_offset += line_height

        cv2.putText(display_frame, f"Available: {available}",
                   (int(panel_x + 10), int(y_offset)), font, font_scale, self.colors['free'], thickness)
        y_offset += line_height

        cv2.putText(display_frame, f"Occupied: {self.occupied_spots}",
                   (int(panel_x + 10), int(y_offset)), font, font_scale, self.colors['occupied'], thickness)
        y_offset += line_height

        # Occupancy percentage
        occupancy_rate = (self.occupied_spots / self.total_spots * 100) if self.total_spots > 0 else 0
        cv2.putText(display_frame, f"Occupancy: {occupancy_rate:.1f}%",
                   (int(panel_x + 10), int(y_offset)), font, font_scale, color, 1)
        y_offset += line_height

        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(display_frame, f"Updated: {timestamp}",
                   (int(panel_x + 10), int(y_offset)), font, 0.4, color, 1)

        return display_frame

    def save_occupancy_data(self, output_path: str = None) -> None:
        """
        Save current occupancy data to JSON file

        Args:
            output_path: Path to save data file
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/results/occupancy_{timestamp}.json"

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        occupancy_data = {
            'timestamp': datetime.now().isoformat(),
            'video_path': self.video_path,
            'total_spots': self.total_spots,
            'occupied_spots': self.occupied_spots,
            'available_spots': self.total_spots - self.occupied_spots,
            'occupancy_rate': (self.occupied_spots / self.total_spots * 100) if self.total_spots > 0 else 0,
            'spots': []
        }

        for spot in self.spots:
            spot_data = {
                'id': spot['id'],
                'type': spot.get('type', 'normal'),
                'occupied': spot['occupied'],
                'confidence': spot.get('confidence', 0.0),
                'last_detection_time': spot.get('last_detection_time', 0)
            }
            occupancy_data['spots'].append(spot_data)

        try:
            with open(output_path, 'w') as f:
                json.dump(occupancy_data, f, indent=2)
            self.logger.info(f"Occupancy data saved to: {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving occupancy data: {str(e)}")

    def run(self, save_output: bool = False, display: bool = True) -> None:
        """
        Run the parking monitoring system

        Args:
            save_output: Whether to save output video
            display: Whether to display video window
        """
        if not self.load_spots_config() or not self.load_video():
            return

        # Initialize car detector
        self.car_detector.use_opencv_dnn()

        self.logger.info("Starting parking lot monitoring...")
        self.logger.info(f"Monitoring {self.total_spots} parking spots")

        # Setup video writer if saving output
        video_writer = None
        if save_output:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = self.video.get(cv2.CAP_PROP_FPS)
            width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/results/parking_monitor_{timestamp}.mp4"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        if display:
            cv2.namedWindow('Parking Monitor', cv2.WINDOW_RESIZABLE)

        try:
            while True:
                ret, frame = self.video.read()
                if not ret:
                    break

                self.frame_count += 1

                # Detect cars in frame
                detections = self.car_detector.detect_cars(frame)

                # Check parking spot occupancy
                self.check_spot_occupancy(frame, detections)

                # Draw car detections
                frame_with_cars = self.car_detector.draw_detections(frame, detections)

                # Draw parking spots
                frame_with_spots = self.draw_spots(frame_with_cars)

                # Draw info panel
                display_frame = self.draw_info_panel(frame_with_spots)

                # Save frame if requested
                if video_writer:
                    video_writer.write(display_frame)

                # Display frame
                if display:
                    cv2.imshow('Parking Monitor', display_frame)

                # Save occupancy data periodically (every 30 seconds)
                current_time = time.time()
                if current_time - self.last_update_time > 30:
                    self.save_occupancy_data()
                    self.last_update_time = current_time

                # Handle key presses
                if display:
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27:  # ESC
                        break
                    elif key == ord('s'):
                        self.save_occupancy_data()
                        self.logger.info("Manual save triggered")

        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")

        finally:
            # Cleanup
            if self.video:
                self.video.release()
            if video_writer:
                video_writer.release()
            if display:
                cv2.destroyAllWindows()

            # Save final occupancy data
            self.save_occupancy_data()
            self.logger.info("Parking monitoring session ended")


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description="Parking Lot Monitoring System")
    parser.add_argument("--video", required=True, help="Path to parking lot video")
    parser.add_argument("--spots", required=True, help="Path to parking spots configuration JSON")
    parser.add_argument("--save", action="store_true", help="Save output video")
    parser.add_argument("--no-display", action="store_true", help="Run without display (headless mode)")

    args = parser.parse_args()

    # Create output directories
    os.makedirs("output/logs", exist_ok=True)
    os.makedirs("output/results", exist_ok=True)

    # Initialize and run monitor
    monitor = ParkingMonitor(args.video, args.spots)
    monitor.run(save_output=args.save, display=not args.no_display)


if __name__ == "__main__":
    main()