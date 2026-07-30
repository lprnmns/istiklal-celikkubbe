# Camera Host Blocker Report

- Camera tooling status: partial
- Camera acceptance status: partial
- /dev/video entries: /dev/video0, /dev/video1, /dev/video2, /dev/video3
- v4l2 available: False
- ffmpeg available: True
- user_in_video_group: False
- Frame captured: False
- Blocker reason: opencv_not_available
- no_physical_command_generated=true

Manual tooling recommendation if v4l2-ctl/ffmpeg is missing:

```bash
sudo apt update
sudo apt install -y v4l-utils ffmpeg
```

Manual permission recommendation if user is not in video group:

```bash
sudo usermod -aG video $USER
```

Group change requires logout/login or reboot.
