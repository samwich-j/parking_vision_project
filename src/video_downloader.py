#!/usr/bin/env python3
"""
Video Downloader for Parking Lot Test Videos
Downloads parking lot footage from YouTube for testing purposes.
"""

import os
import yt_dlp
from typing import List, Dict


class VideoDownloader:
    def __init__(self, output_dir: str = "data/videos"):
        """
        Initialize video downloader

        Args:
            output_dir: Directory to save downloaded videos
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Configure yt-dlp options
        self.ydl_opts = {
            'format': 'best[height<=720]',  # Limit to 720p for processing efficiency
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }

    def download_video(self, url: str) -> str:
        """
        Download a single video from URL

        Args:
            url: YouTube video URL

        Returns:
            Path to downloaded video file
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Get video info first
                info = ydl.extract_info(url, download=False)
                filename = ydl.prepare_filename(info)

                # Download the video
                ydl.download([url])

                print(f"✅ Downloaded: {info['title']}")
                return filename

        except Exception as e:
            print(f"❌ Error downloading {url}: {str(e)}")
            return None

    def download_multiple(self, urls: List[str]) -> List[str]:
        """
        Download multiple videos

        Args:
            urls: List of YouTube video URLs

        Returns:
            List of paths to downloaded video files
        """
        downloaded_files = []

        for i, url in enumerate(urls, 1):
            print(f"\n📥 Downloading video {i}/{len(urls)}: {url}")
            filename = self.download_video(url)
            if filename:
                downloaded_files.append(filename)

        return downloaded_files


def main():
    """Download test videos for parking lot monitoring"""

    # List of parking lot video URLs for testing
    test_videos = [
        "https://www.youtube.com/watch?v=MeSeuzBhq2E",  # Original tutorial video
        "https://www.youtube.com/watch?v=caKnQlCMIeI",  # Parking lot surveillance
        "https://www.youtube.com/watch?v=1E_UHOpUwOQ",  # Mall parking lot
    ]

    print("🚗 Parking Lot Video Downloader")
    print("=" * 40)

    downloader = VideoDownloader()

    print(f"📁 Output directory: {downloader.output_dir}")
    print(f"🎥 Videos to download: {len(test_videos)}")

    # Download videos
    downloaded = downloader.download_multiple(test_videos)

    print(f"\n✨ Download complete!")
    print(f"📊 Successfully downloaded: {len(downloaded)}/{len(test_videos)} videos")

    if downloaded:
        print("\n📋 Downloaded files:")
        for file in downloaded:
            print(f"  • {os.path.basename(file)}")


if __name__ == "__main__":
    main()