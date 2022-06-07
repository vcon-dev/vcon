
certs: fake_grp.crt fake_div.crt expired_div.crt fake_ca2_root.crt

# Create expired sub divisions cert in the chain below root
expired_div.crt: expired_div.key ca.key
	openssl x509 -req -days 1 -passin pass:fake -in expired_div.csr -CA fake_ca_root.crt -CAkey ca.key -set_serial 01 -out expired_div.crt

expired_div.key: fake_ca_root.crt   
	openssl req -newkey rsa:2048 -nodes -subj /C=US/ST=MA/L=Faketown/O=FakeVcon/OU=Division/CN=div.fakevcon.io/emailAddress=admin@fakevcon.org/subjectAltName=div.fakevcon.org -keyout expired_div.key -out expired_div.csr

# Create a sub divisions cert in the chain below root
fake_grp.crt: fake_grp.key fake_div.key
	openssl x509 -req -days 3650 -passin pass:fake -in fake_grp.csr -CA fake_div.crt -CAkey fake_div.key -set_serial 01 -out fake_grp.crt

fake_grp.key: fake_div.crt   
	openssl req -newkey rsa:2048 -nodes -subj /C=US/ST=MA/L=Faketown/O=FakeVcon/OU=Group/CN=grp.div.fakevcon.io/emailAddress=admin@fakevcon.org/subjectAltName=grp.div.fakevcon.org -keyout fake_grp.key -out fake_grp.csr

# Create a sub divisions cert in the chain below root
fake_div.crt: fake_div.key ca.key
	openssl x509 -req -days 3650 -passin pass:fake -in fake_div.csr -CA fake_ca_root.crt -CAkey ca.key -set_serial 02 -out fake_div.crt

fake_div.key: fake_ca_root.crt   
	openssl req -newkey rsa:2048 -nodes -subj /C=US/ST=MA/L=Faketown/O=FakeVcon/OU=Division/CN=div.fakevcon.io/emailAddress=admin@fakevcon.org/subjectAltName=div.fakevcon.org -keyout fake_div.key -out fake_div.csr

# Sign the CA
fake_ca_root.crt: ca.key
	openssl req -new -x509 -passin pass:fake -days 3650 -key ca.key -subj /C=US/ST=MA/L=Faketown/O=FakeVcon\ Inc/OU=Corporate/CN=fakevcon.io/emailAddress=admin@fakevcon.org/subjectAltName=fakevcon.org -keyout fake_root.key -out fake_ca_root.crt

# Create certificate of authority (CA) key
ca.key: 
	openssl genrsa -des3 -passout pass:fake -out ca.key 4096
	chmod 600 ca.key

# Sign the second CA
fake_ca2_root.crt: ca2.key
	openssl req -new -x509 -passin pass:fake -days 3650 -key ca2.key -subj /C=US/ST=MA/L=Faketown/O=FakeVcon\ Inc/OU=Corporate/CN=fakevcon.io/emailAddress=admin@fakevcon.org/subjectAltName=fakevcon.org -keyout fake_root.key -out fake_ca2_root.crt

# Create another certificate of authority (CA) key
ca2.key: 
	openssl genrsa -des3 -passout pass:fake -out ca2.key 4096
	chmod 600 ca2.key
