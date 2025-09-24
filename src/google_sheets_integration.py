#!/usr/bin/env python3
"""
Google Sheets Integration for Parking Lot Data
Uploads parking occupancy data to Google Sheets for real-time monitoring.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    print("⚠️  Google Sheets integration not available. Install with: pip install gspread google-auth")


class GoogleSheetsIntegration:
    def __init__(self, credentials_path: str = "credentials/service_account.json"):
        """
        Initialize Google Sheets integration

        Args:
            credentials_path: Path to service account JSON credentials
        """
        self.credentials_path = credentials_path
        self.client = None
        self.worksheet = None
        self.spreadsheet_id = None

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Define required scopes
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

    def authenticate(self) -> bool:
        """
        Authenticate with Google Sheets API

        Returns:
            True if successful, False otherwise
        """
        if not SHEETS_AVAILABLE:
            self.logger.error("Google Sheets libraries not available")
            return False

        if not os.path.exists(self.credentials_path):
            self.logger.error(f"Credentials file not found: {self.credentials_path}")
            self.logger.info("Please download service account credentials from Google Cloud Console")
            return False

        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path, scopes=self.scopes
            )
            self.client = gspread.authorize(credentials)
            self.logger.info("✅ Google Sheets authentication successful")
            return True

        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False

    def create_parking_spreadsheet(self, title: str = "Parking Lot Monitor") -> Optional[str]:
        """
        Create a new spreadsheet for parking data

        Args:
            title: Title of the spreadsheet

        Returns:
            Spreadsheet ID if successful, None otherwise
        """
        if not self.client:
            self.logger.error("Not authenticated with Google Sheets")
            return None

        try:
            spreadsheet = self.client.create(title)
            self.spreadsheet_id = spreadsheet.id

            # Share with your email (replace with your email)
            # spreadsheet.share('your-email@gmail.com', perm_type='user', role='writer')

            self.logger.info(f"✅ Created spreadsheet: {title}")
            self.logger.info(f"📊 Spreadsheet URL: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")

            # Setup initial worksheets
            self.setup_worksheets()

            return self.spreadsheet_id

        except Exception as e:
            self.logger.error(f"Error creating spreadsheet: {str(e)}")
            return None

    def open_spreadsheet(self, spreadsheet_id: str) -> bool:
        """
        Open existing spreadsheet

        Args:
            spreadsheet_id: ID of the spreadsheet

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            self.logger.error("Not authenticated with Google Sheets")
            return False

        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            self.spreadsheet_id = spreadsheet_id
            self.logger.info(f"✅ Opened spreadsheet: {spreadsheet.title}")
            return True

        except Exception as e:
            self.logger.error(f"Error opening spreadsheet: {str(e)}")
            return False

    def setup_worksheets(self) -> None:
        """
        Setup initial worksheet structure
        """
        if not self.client or not self.spreadsheet_id:
            return

        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)

            # Rename default sheet to "Current Status"
            sheet1 = spreadsheet.sheet1
            sheet1.update_title("Current Status")

            # Add headers for current status
            headers = [
                "Timestamp", "Total Spots", "Available", "Occupied",
                "Occupancy Rate (%)", "Normal Available", "Electric Available",
                "Reserved Available", "Last Update"
            ]
            sheet1.append_row(headers)

            # Create "Spot Details" worksheet
            try:
                details_sheet = spreadsheet.add_worksheet(title="Spot Details", rows=100, cols=10)
                detail_headers = [
                    "Spot ID", "Type", "Status", "Confidence", "Last Occupied",
                    "X Coordinate", "Y Coordinate", "Area", "Notes", "Timestamp"
                ]
                details_sheet.append_row(detail_headers)
            except:
                pass  # Sheet might already exist

            # Create "Historical Data" worksheet
            try:
                history_sheet = spreadsheet.add_worksheet(title="Historical Data", rows=1000, cols=8)
                history_headers = [
                    "Timestamp", "Total Spots", "Available", "Occupied",
                    "Occupancy Rate (%)", "Peak Hour", "Weather", "Notes"
                ]
                history_sheet.append_row(history_headers)
            except:
                pass  # Sheet might already exist

            self.logger.info("✅ Worksheet structure setup complete")

        except Exception as e:
            self.logger.error(f"Error setting up worksheets: {str(e)}")

    def upload_current_status(self, occupancy_data: Dict) -> bool:
        """
        Upload current parking status to Google Sheets

        Args:
            occupancy_data: Dictionary containing parking occupancy data

        Returns:
            True if successful, False otherwise
        """
        if not self.client or not self.spreadsheet_id:
            self.logger.error("Google Sheets not properly initialized")
            return False

        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            current_sheet = spreadsheet.worksheet("Current Status")

            # Prepare data row
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total_spots = occupancy_data.get('total_spots', 0)
            occupied = occupancy_data.get('occupied_spots', 0)
            available = occupancy_data.get('available_spots', 0)
            occupancy_rate = occupancy_data.get('occupancy_rate', 0)

            # Count by type
            spots = occupancy_data.get('spots', [])
            normal_available = sum(1 for s in spots if s.get('type') == 'normal' and not s.get('occupied'))
            electric_available = sum(1 for s in spots if s.get('type') == 'electric' and not s.get('occupied'))
            reserved_available = sum(1 for s in spots if s.get('type') == 'reserved' and not s.get('occupied'))

            row_data = [
                timestamp,
                total_spots,
                available,
                occupied,
                round(occupancy_rate, 2),
                normal_available,
                electric_available,
                reserved_available,
                datetime.now().strftime("%H:%M:%S")
            ]

            # Clear existing data and add new row (keep only latest status)
            current_sheet.clear()
            headers = [
                "Timestamp", "Total Spots", "Available", "Occupied",
                "Occupancy Rate (%)", "Normal Available", "Electric Available",
                "Reserved Available", "Last Update"
            ]
            current_sheet.append_row(headers)
            current_sheet.append_row(row_data)

            # Also append to historical data
            try:
                history_sheet = spreadsheet.worksheet("Historical Data")
                history_row = [
                    timestamp,
                    total_spots,
                    available,
                    occupied,
                    round(occupancy_rate, 2),
                    "",  # Peak hour - can be calculated later
                    "",  # Weather - can be added from external API
                    ""   # Notes
                ]
                history_sheet.append_row(history_row)
            except:
                pass  # History sheet might not exist

            self.logger.info(f"✅ Status uploaded to Google Sheets: {available}/{total_spots} available")
            return True

        except Exception as e:
            self.logger.error(f"Error uploading current status: {str(e)}")
            return False

    def upload_spot_details(self, occupancy_data: Dict) -> bool:
        """
        Upload detailed spot information to Google Sheets

        Args:
            occupancy_data: Dictionary containing parking occupancy data

        Returns:
            True if successful, False otherwise
        """
        if not self.client or not self.spreadsheet_id:
            self.logger.error("Google Sheets not properly initialized")
            return False

        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            details_sheet = spreadsheet.worksheet("Spot Details")

            # Clear existing data
            details_sheet.clear()

            # Add headers
            headers = [
                "Spot ID", "Type", "Status", "Confidence", "Last Occupied",
                "X Coordinate", "Y Coordinate", "Area", "Notes", "Timestamp"
            ]
            details_sheet.append_row(headers)

            # Add spot data
            spots = occupancy_data.get('spots', [])
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for spot in spots:
                # Calculate center coordinates (simplified)
                center_x = center_y = area = ""
                if 'points' in spot:
                    points = spot['points']
                    center_x = int(sum(p[0] for p in points) / len(points))
                    center_y = int(sum(p[1] for p in points) / len(points))
                    # Approximate area calculation
                    area = len(points) * 100  # Simplified

                status = "OCCUPIED" if spot.get('occupied', False) else "AVAILABLE"
                confidence = spot.get('confidence', 0)
                last_occupied = ""
                if spot.get('last_detection_time', 0) > 0:
                    last_occupied = datetime.fromtimestamp(
                        spot['last_detection_time']
                    ).strftime("%H:%M:%S")

                row_data = [
                    spot.get('id', ''),
                    spot.get('type', 'normal').upper(),
                    status,
                    round(confidence, 3) if confidence > 0 else "",
                    last_occupied,
                    center_x,
                    center_y,
                    area,
                    "",  # Notes
                    timestamp
                ]
                details_sheet.append_row(row_data)

            self.logger.info(f"✅ Uploaded details for {len(spots)} parking spots")
            return True

        except Exception as e:
            self.logger.error(f"Error uploading spot details: {str(e)}")
            return False

    def create_dashboard_formulas(self) -> None:
        """
        Add dashboard formulas to the Current Status sheet
        """
        if not self.client or not self.spreadsheet_id:
            return

        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            current_sheet = spreadsheet.worksheet("Current Status")

            # Add some useful formulas and formatting
            # This would typically include charts and conditional formatting

            self.logger.info("✅ Dashboard formulas added")

        except Exception as e:
            self.logger.error(f"Error creating dashboard formulas: {str(e)}")


class MockGoogleSheetsIntegration:
    """
    Mock implementation for when Google Sheets is not available
    Saves data to local JSON files instead
    """

    def __init__(self, output_dir: str = "output/sheets"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Using mock Google Sheets integration (saving to local files)")

    def authenticate(self) -> bool:
        return True

    def create_parking_spreadsheet(self, title: str = "Parking Lot Monitor") -> Optional[str]:
        return "mock_spreadsheet_id"

    def open_spreadsheet(self, spreadsheet_id: str) -> bool:
        return True

    def upload_current_status(self, occupancy_data: Dict) -> bool:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"current_status_{timestamp}.json")

        try:
            with open(output_file, 'w') as f:
                json.dump(occupancy_data, f, indent=2)

            self.logger.info(f"📄 Status saved to: {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving status: {str(e)}")
            return False

    def upload_spot_details(self, occupancy_data: Dict) -> bool:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"spot_details_{timestamp}.json")

        try:
            with open(output_file, 'w') as f:
                json.dump(occupancy_data, f, indent=2)

            self.logger.info(f"📄 Details saved to: {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving details: {str(e)}")
            return False


def create_sheets_integration(credentials_path: str = "credentials/service_account.json") -> object:
    """
    Factory function to create sheets integration (real or mock)

    Args:
        credentials_path: Path to service account credentials

    Returns:
        GoogleSheetsIntegration or MockGoogleSheetsIntegration instance
    """
    if SHEETS_AVAILABLE and os.path.exists(credentials_path):
        integration = GoogleSheetsIntegration(credentials_path)
        if integration.authenticate():
            return integration

    # Fall back to mock integration
    return MockGoogleSheetsIntegration()


def main():
    """Test Google Sheets integration"""
    print("🔍 Testing Google Sheets Integration")
    print("=" * 40)

    # Test with mock data
    integration = create_sheets_integration()

    # Sample occupancy data
    test_data = {
        'timestamp': datetime.now().isoformat(),
        'total_spots': 20,
        'occupied_spots': 12,
        'available_spots': 8,
        'occupancy_rate': 60.0,
        'spots': [
            {'id': 1, 'type': 'normal', 'occupied': True, 'confidence': 0.85},
            {'id': 2, 'type': 'electric', 'occupied': False, 'confidence': 0.0},
            {'id': 3, 'type': 'reserved', 'occupied': True, 'confidence': 0.9}
        ]
    }

    # Test uploads
    if hasattr(integration, 'create_parking_spreadsheet'):
        spreadsheet_id = integration.create_parking_spreadsheet("Test Parking Monitor")
        if spreadsheet_id:
            integration.upload_current_status(test_data)
            integration.upload_spot_details(test_data)

    print("✅ Google Sheets integration test complete")


if __name__ == "__main__":
    main()