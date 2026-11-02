# Essensliste

Hier gehts um die Erstellung der wöchentlichen Menükarte von Emmas Imbiss (https://menu.mama-filmcatering.com/).

## WhatsApp-Testeingang

Nachrichten werden zunächst im Django-Admin unter „Abrechnung / WhatsApp-Nachrichten“ gepflegt.
Beim Speichern wird ein Kunde anhand der internationalen Absendernummer eindeutig zugeordnet.
Ist die Nummer unbekannt oder mehrfach vergeben, muss der Kunde manuell ausgewählt werden.

Das Speichern einer noch nicht verarbeiteten Nachricht wertet deren Text mit einem lokalen
Ollama-Modell aus und legt ungeprüfte Bestellungen je Tag an. Relative Datumsangaben beziehen
sich auf „Empfangen am“. Der vollständige Originaltext wird bei jedem Tag gespeichert.
Gerichte und Preise werden anhand des Speiseplans des jeweiligen Tages zugeordnet.
Bei Wahlessen wird die gewählte Hauptspeise mit der Beilagenalternative verbunden.
Ohne ausdrückliche Beilagenwahl gilt die erste Alternative in der Plansortierung.
Sonderwünsche bleiben im Kommentar erhalten. Ein rotes „€?“ markiert Preise zur Prüfung,
auch wenn wegen eines Sonderwunsches zunächst der reguläre Menüpreis übernommen wurde.
Bei fehlender oder mehrdeutiger Zuordnung bleibt der Preis 0. Eine Preiskorrektur oder
die Abnahme der Bestellung entfernt die Markierung.
Die Lieferansicht zeigt heutige Bestellungen sowie alle noch vorläufigen Bestelltage.
Die Filter „Alle“, „Vorläufig“ und „Abgenommen“ ermöglichen die zentrale Prüfung mit Originalnachricht.
Das Badge auf der Kundenübersicht zählt alle noch ungeprüften, nicht abgerechneten Bestelltage
mit Positionen, einschließlich zukünftiger Termine. Ein Klick öffnet direkt den Filter „Vorläufig“.

„Bestellungen angelegt am“ schützt vor erneutem Import derselben Nachricht. Spätere Änderungen
an bereits verarbeiteten Nachrichten ändern bestehende Bestellungen nicht. Korrekturen erfolgen
in der Tagesübersicht. Bei fehlendem Kunden, unklarem Inhalt oder einem KI-Ausfall bleibt die
Nachricht mit einem Verarbeitungshinweis gespeichert. Erneutes Speichern versucht die Auswertung erneut.

Die Auswertung läuft synchron beim Speichern und benötigt einen erreichbaren lokalen Ollama-Dienst.
Konfiguration: `WHATSAPP_OLLAMA_URL` (Standard `http://127.0.0.1:11434`) und
`WHATSAPP_OLLAMA_MODEL` (Standard `qwen3:8b-q4_K_M`). Andys lokale Entwicklungseinstellungen
verwenden den bereits laufenden Dienst auf `192.168.188.57:11434`.
Es gibt noch keine echte WhatsApp-Anbindung. Modelle werden nicht automatisch heruntergeladen.

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
