# PIA ICS

Applicazione Django per la gestione di macchine, assistenze e tracciamento.

## Avvio locale

1. Creare e attivare un ambiente virtuale Python.
2. Installare le dipendenze: `pip install -r pia_ics/requirements.txt`.
3. Esportare le variabili indicate in `.env.example` (il file non viene letto automaticamente).
4. Dalla cartella `pia_ics`, eseguire `python manage.py migrate` e `python manage.py runserver`.

Per un avvio di sviluppo senza MySQL, non impostare `DJANGO_DB_ENGINE` e `DJANGO_DB_NAME`: viene usato SQLite locale, escluso dal controllo versione.

## Configurazione sensibile

Le credenziali del database, la chiave Django e l'account di servizio Google non devono essere inseriti nel repository. Configurarli esclusivamente tramite variabili d'ambiente; il JSON dell'account Google deve restare esterno al repository e il suo percorso va impostato con `GOOGLE_APPLICATION_CREDENTIALS`.

## Pubblicazione Open Source

Prima della pubblicazione scegliere e aggiungere una licenza esplicita. Verificare inoltre che eventuali chiavi già esposte siano state revocate e rigenerate.

## Import dati di produzione (PIA_FEMA)

La tracciabilità legge ordini, commesse, blocchi e log macchina importati dal DB SQL Server `PIA_FEMA` (schemi `dbo`, `wms`, `NEXUM`), che sostituisce i vecchi database `PIA_FemaWms` e `PIA_FEMA_PRODPLAN`.

1. Impostare le variabili `FEMA_DB_*` indicate in `.env.example`.
2. Dalla cartella `pia_ics` eseguire `python manage.py importa_fema` (opzione `--cliente-id <id>` se in piattaforma esistono più clienti a cui associare le macchine nuove).

Il comando è ripetibile: aggiorna i dati esistenti e importa solo i log macchina nuovi. Le soglie di qualità (`QualitàAngoloAutomatico`, `QualitàTaglio`) vanno configurate dall'admin.

### Ripristino locale del backup

```bash
docker run -d --name pia_fema_sql -e ACCEPT_EULA=Y -e "MSSQL_SA_PASSWORD=<password>" -p 14333:1433 \
  -v "<cartella con PIA_FEMA.bak>:/backup:ro" mcr.microsoft.com/mssql/server:2022-latest
docker exec pia_fema_sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "<password>" -C -Q \
  "RESTORE DATABASE PIA_FEMA FROM DISK='/backup/PIA_FEMA.bak' WITH MOVE 'FEMA' TO '/var/opt/mssql/data/PIA_FEMA.mdf', MOVE 'FEMA_log' TO '/var/opt/mssql/data/PIA_FEMA_log.ldf'"
```
