if [ -z "$METADATA_URL" ]
then
  echo "Using Mounted local metadata"
else
  echo "Using metadata: $METADATA_URL"
  mkdir /metadata
  wget "$METADATA_URL" -O /metadata/idpssodescriptor.xml --no-check-certificate
fi

if [ -z "$MODE" ]
then
  echo "Running in direct logoff mode"
  python3 sp_directlogoff.py -C service_conf sp_conf
else
  echo "Running in normal mode"
  python3 sp.py -C service_conf sp_conf
fi
