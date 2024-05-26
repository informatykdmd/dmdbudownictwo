import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mysqlDB import connect_to_database
from bin.appslib import handle_error

global smtp_config
smtp_config = {
    'smtp_server': connect_to_database(f'SELECT admin_smtp_server FROM admin_settings;')[0][0],
    'smtp_port': connect_to_database(f'SELECT admin_smtp_port FROM admin_settings;')[0][0],  # Domyślny port dla TLS
    'smtp_username': connect_to_database(f'SELECT admin_smtp_usernam FROM admin_settings;')[0][0],
    'smtp_password': connect_to_database(f'SELECT admin_smtp_password FROM admin_settings;')[0][0]
}



def send_html_email(subject, html_body, to_email):
    try:
        # Utwórz wiadomość
        message = MIMEMultipart()
        smtp_server = smtp_config['smtp_server']
        smtp_port =smtp_config['smtp_port']
        smtp_username = smtp_config['smtp_username']
        smtp_password = smtp_config['smtp_password']
        message["From"] = smtp_username
        message["To"] = to_email
        message["Subject"] = subject
        

        # Dodaj treść HTML
        message.attach(MIMEText(html_body, "html"))

        # Utwórz połączenie z serwerem SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Rozszerzenie STARTTLS
            server.starttls()
            # Zaloguj się do konta SMTP
            server.login(smtp_username, smtp_password)

            # Wyślij wiadomość
            server.sendmail(smtp_username, to_email, message.as_string())
    except Exception as e:
        handle_error(f'Wysyłanie  maila do {to_email} nieudane: {e}', log_path='./log/errors.log')

if __name__ == "__main__":
    
    # Przykładowe dane
    subject = "Testy"
    html_body = "<html><body><h1>Witaj!</h1><p>To jest treść wiadomości HTML.</p></body></html>"
    to_email = "informatyk@dmdbudownictwo.pl"


    # Wywołaj funkcję wysyłania e-maila HTML
    send_html_email(subject, html_body, to_email)
