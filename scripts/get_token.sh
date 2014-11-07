echo "Gettings token from http://$1/token.php?token=$2"
curl http://$1/token.php?token=$2
echo ""

