# Any Video Downloader

A modern, sleek, and powerful video downloader application aimed at providing better user experience. Built with Python and CustomTkinter, it supports downloading videos and playlists from YouTube, Vimeo, and many other platforms.

## 🚀 Features

-   **Multi-Platform Support**: Downloads from YouTube, Vimeo, and supported `yt-dlp` sites.
-   **Smart Analysis**: Automatically detects video metadata, available resolutions, and playlist info.
-   **Format Selection**: Choose from 1080p, 720p, etc., or convert directly to **MP3** (High/Medium/Low quality).
-   **Playlist Support**: Batch download entire playlists with index tracking.
-   **Modern UI**: A beautiful "Dark Mode" interface inspired by modern design principles.
-   **Download History**: Keeps track of your downloads. Resume or retry downloads directly from the history panel.
-   **Real-time Progress**: Displays download speed, ETA, and percentage.
-   **Control**: Pause and Cancel functionality.

## 🛠️ Prerequisites

-   **Python 3.8+**
-   **FFmpeg**: Required for audio conversion and merging video/audio streams.
    -   *Windows*: [Download FFmpeg](https://ffmpeg.org/download.html) and add it to your system PATH.
    -   *Mac*: `brew install ffmpeg`
    -   *Linux*: `sudo apt install ffmpeg`

## 📦 Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/Talion-101/any-video-downloader.git
    cd any-video-downloader
    ```

2.  Install the required Python packages:
    ```bash
    pip install customtkinter yt-dlp Pillow requests
    ```

## ▶️ Usage

1.  Run the application:
    ```bash
    python main.py
    ```

2.  **Paste a URL** (Video or Playlist) into the search bar.
3.  Click **Analyze**.
4.  Select your preferred **Video Quality** or **Audio Format**.
5.  Click **Download Now**.
6.  Files are saved to the `downloads/` directory.

## 📂 Project Structure

-   `main.py`: Entry point of the application.
-   `app/ui/`: Contains all GUI components (`MainWindow`, `HistoryPanel`) and theme settings.
-   `app/core/`: Contains core logic for downloading (`downloader.py`) and history management (`history.py`).
-   `downloads/`: Default video save location.
-   `history.json`: Stores your download history data.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

