using System.Threading.Tasks;

namespace Laundrymeter.Services
{
    // This class is used by the application to send email for account confirmation and password reset.
    // For more details see https://go.microsoft.com/fwlink/?LinkID=532713
    public class EmailSenderService
    {
        public Task SendEmailAsync(string email, string subject, string message)
        {
            return Task.CompletedTask;

            // var message = new MimeMessage ();
            // message.From.Add(new MailboxAddress("No-reply", "noreply@myblog.io"));
            // message.To.Add(new MailboxAddress(<to>, <to>));
            // message.Subject = "New e-mail";
            // message.Body = new TextPart("plain") {
            //     Text = "Wow, a MailKit e-mail";
            // }

            // using (var client = new SmtpClient ()) {
            //     // For demo-purposes, accept all SSL certificates (in case the server supports STARTTLS)
            //     client.ServerCertificateValidationCallback = (s,c,h,e) => true;

            //     client.Connect (<your server>, <your port>, false);

            //     // Note: since we don't have an OAuth2 token, disable
            //     // the XOAUTH2 authentication mechanism.
            //     client.AuthenticationMechanisms.Remove ("XOAUTH2");

            //     // Note: only needed if the SMTP server requires authentication
            //     client.Authenticate(<user>, <pwd>);

            //     client.Send (message);
            //     client.Disconnect (true);
            // }
        }
    }
}