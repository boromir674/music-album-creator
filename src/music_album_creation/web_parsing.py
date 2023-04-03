from pytube import YouTube


def video_title(youtube_url: str) -> str:
    video = YouTube(youtube_url)
    return video.title
