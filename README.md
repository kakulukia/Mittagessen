# Essensliste

Hier gehts um die Erstellung der wöchentlichen Menükarte von Emmas Imbiss (https://menu.mama-filmcatering.com/).

##### Deployment

    yarn build && scp -r dist mamasystems.de:/opt/www/mittag/speisekarte/



## alte nginx config

access_log /opt/www/logs/mittag-access.log;
error_log /opt/www/logs/mittag-error.log;

location /static/ {
	alias   /opt/www/mittag/static/;
}

location /media/ {
	alias   /opt/www/mittag/media/;
}

location /kueche/ {
	alias   /opt/www/mittag/speisekarte/dist/;
}

location / {
	proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	proxy_set_header Host $http_host;
	proxy_redirect off;

	if (!-f $request_filename) {
		proxy_pass http://unix:/tmp/mittag.sock;
		break;
	}
}
