echo "Installing FBI"
apt-get install fbi
echo "Creating Splashscript init scripts"
cat <<\EOF > /etc/init.d/msplashscreen &&
#! /bin/sh
### BEGIN INIT INFO
# Provides:          msplashscreen
# Required-Start:
# Required-Stop:
# Should-Start:      
# Default-Start:     S
# Default-Stop:
# Short-Description: Show custom splashscreen
# Description:       Show custom splashscreen
### END INIT INFO


do_start () {
    fbi -T 2 -d /dev/fb1 -noverbose -a /home/pi/code/kana_TFT/splash/splash_loading.png
    #mplayer -vo fbdev2:/dev/fb1 /home/pi/code/splash2.mp4 &
    exit 0
}

case "$1" in
  start|"")
    do_start
    ;;
  restart|reload|force-reload)
    echo "Error: argument '$1' not supported" >&2
    exit 3
    ;;
  stop)
    # No-op
    ;;
  status)
    exit 0
    ;;
  *)
    echo "Usage: msplashscreen [start|stop]" >&2
    exit 3
    ;;
esac
EOF
echo "Make script executable"
chmod +x /etc/init.d/msplashscreen
echo "Insert at startup"
insserv /etc/init.d/msplashscreen
