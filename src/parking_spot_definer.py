#!/usr/bin/env python3
"""
Parking Spot Definition Tool
Allows users to manually define parking spot regions in parking lot videos.
"""

import cv2
import numpy as np
import json
import os
from typing import List, Tuple, Dict, Optional


class ParkingSpotDefiner:
    def __init__(self, video_path: str):
        """
        Initialize parking spot definer

        Args:
            video_path: Path to parking lot video
        """
        self.video_path = video_path
        self.video = None
        self.frame = None
        self.spots = []
        self.current_spot = []
        self.drawing = False
        self.spot_counter = 1

        # Colors for different spot types
        self.colors = {
            'normal': (0, 255, 0),      # Green for normal spots
            'electric': (255, 255, 0),   # Cyan for electric spots
            'reserved': (0, 0, 255),     # Red for reserved spots
            'current': (255, 0, 255)     # Magenta for current drawing
        }

        self.current_spot_type = 'normal'

    def load_video(self) -> bool:
        """
        Load video file

        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.video_path):
            print(f"❌ Video file not found: {self.video_path}")
            return False

        self.video = cv2.VideoCapture(self.video_path)
        if not self.video.isOpened():
            print(f"❌ Could not open video: {self.video_path}")
            return False

        # Get first frame
        ret, frame = self.video.read()
        if not ret:
            print("❌ Could not read video frame")
            return False

        self.frame = frame.copy()
        print(f"✅ Video loaded: {self.video_path}")
        print(f"📐 Frame size: {frame.shape[1]}x{frame.shape[0]}")
        return True

    def mouse_callback(self, event, x, y, flags, param):
        """
        Handle mouse events for drawing parking spots

        Args:
            event: Mouse event type
            x, y: Mouse coordinates
            flags: Additional flags
            param: Additional parameters
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            self.current_spot.append((x, y))
            print(f"📍 Point added: ({x}, {y})")

        elif event == cv2.EVENT_RBUTTONDOWN:
            if len(self.current_spot) >= 3:
                # Complete the current spot
                spot_data = {
                    'id': self.spot_counter,
                    'points': self.current_spot.copy(),
                    'type': self.current_spot_type,
                    'occupied': False
                }
                self.spots.append(spot_data)
                print(f"✅ Spot {self.spot_counter} ({self.current_spot_type}) created with {len(self.current_spot)} points")
                self.spot_counter += 1
                self.current_spot = []
            else:
                print("❌ Need at least 3 points to create a parking spot")

    def draw_interface(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw the user interface on the frame

        Args:
            frame: Input frame

        Returns:
            Frame with UI elements drawn
        """
        display_frame = frame.copy()

        # Draw existing spots
        for spot in self.spots:
            points = np.array(spot['points'], np.int32)
            color = self.colors.get(spot['type'], self.colors['normal'])

            # Draw filled polygon for parking spot
            cv2.fillPoly(display_frame, [points], color + (100,))  # Semi-transparent fill

            # Draw outline
            cv2.polylines(display_frame, [points], True, color, 2)

            # Draw spot ID
            center_x = int(np.mean([p[0] for p in spot['points']]))
            center_y = int(np.mean([p[1] for p in spot['points']]))
            cv2.putText(display_frame, str(spot['id']), (center_x-10, center_y+5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Draw current spot being defined
        if len(self.current_spot) >= 2:
            points = np.array(self.current_spot, np.int32)
            cv2.polylines(display_frame, [points], False, self.colors['current'], 2)

        # Draw current point
        if len(self.current_spot) >= 1:
            for point in self.current_spot:
                cv2.circle(display_frame, point, 5, self.colors['current'], -1)

        # Draw instructions
        instructions = [
            f"Current type: {self.current_spot_type.upper()}",
            "Left click: Add point",
            "Right click: Complete spot",
            "Keys: n=Normal, e=Electric, r=Reserved",
            "Keys: s=Save, c=Clear all, u=Undo last",
            "ESC: Exit"
        ]

        y_offset = 30
        for instruction in instructions:
            cv2.putText(display_frame, instruction, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(display_frame, instruction, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            y_offset += 25

        # Draw spot count
        spot_count = f"Total spots: {len(self.spots)}"
        cv2.putText(display_frame, spot_count, (10, display_frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return display_frame

    def save_spots(self, output_path: str = None) -> bool:
        """
        Save defined parking spots to JSON file

        Args:
            output_path: Path to save spots file

        Returns:
            True if successful, False otherwise
        """
        if not output_path:
            base_name = os.path.splitext(os.path.basename(self.video_path))[0]
            output_path = f"data/configs/{base_name}_spots.json"

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        spots_data = {
            'video_path': self.video_path,
            'frame_size': [self.frame.shape[1], self.frame.shape[0]],
            'spots': self.spots,
            'total_spots': len(self.spots),
            'spot_types': {
                'normal': len([s for s in self.spots if s['type'] == 'normal']),
                'electric': len([s for s in self.spots if s['type'] == 'electric']),
                'reserved': len([s for s in self.spots if s['type'] == 'reserved'])
            }
        }

        try:
            with open(output_path, 'w') as f:
                json.dump(spots_data, f, indent=2)
            print(f"✅ Spots saved to: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving spots: {str(e)}")
            return False

    def load_spots(self, spots_path: str) -> bool:
        """
        Load previously defined parking spots

        Args:
            spots_path: Path to spots JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(spots_path, 'r') as f:
                spots_data = json.load(f)

            self.spots = spots_data['spots']
            self.spot_counter = len(self.spots) + 1

            print(f"✅ Loaded {len(self.spots)} parking spots")
            return True
        except Exception as e:
            print(f"❌ Error loading spots: {str(e)}")
            return False

    def run(self):
        """
        Run the interactive spot definition tool
        """
        if not self.load_video():
            return

        window_name = "Parking Spot Definer"
        cv2.namedWindow(window_name, cv2.WINDOW_RESIZABLE)
        cv2.setMouseCallback(window_name, self.mouse_callback)

        print("\n🚗 Parking Spot Definition Tool")
        print("=" * 40)
        print("Instructions:")
        print("• Left click to add points for parking spot corners")
        print("• Right click to complete a parking spot")
        print("• Press 'n' for normal spots, 'e' for electric, 'r' for reserved")
        print("• Press 's' to save, 'c' to clear all, 'u' to undo last spot")
        print("• Press ESC to exit")
        print()

        while True:
            display_frame = self.draw_interface(self.frame)
            cv2.imshow(window_name, display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC key
                break
            elif key == ord('n'):
                self.current_spot_type = 'normal'
                print("🟢 Switched to NORMAL spots")
            elif key == ord('e'):
                self.current_spot_type = 'electric'
                print("🔋 Switched to ELECTRIC spots")
            elif key == ord('r'):
                self.current_spot_type = 'reserved'
                print("🔴 Switched to RESERVED spots")
            elif key == ord('s'):
                self.save_spots()
            elif key == ord('c'):
                self.spots = []
                self.current_spot = []
                self.spot_counter = 1
                print("🗑️  All spots cleared")
            elif key == ord('u'):
                if self.spots:
                    removed_spot = self.spots.pop()
                    self.spot_counter = max(1, self.spot_counter - 1)
                    print(f"↩️  Undid spot {removed_spot['id']}")
                else:
                    print("❌ No spots to undo")

        cv2.destroyAllWindows()
        if self.video:
            self.video.release()


def main():
    """Run the parking spot definer"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parking_spot_definer.py <video_path>")
        print("Example: python parking_spot_definer.py data/videos/parking_lot.mp4")
        return

    video_path = sys.argv[1]
    definer = ParkingSpotDefiner(video_path)
    definer.run()


if __name__ == "__main__":
    main()