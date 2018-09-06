using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Options;

using Telegram.Bot;
using Telegram.Bot.Types;
using Telegram.Bot.Types.Enums;
using Laundrymeter.Settings;
using Laundrymeter.Services;

namespace Laundrymeter.Services
{
    // This class is used by the application to send email for account confirmation and password reset.
    // For more details see https://go.microsoft.com/fwlink/?LinkID=532713

    public class TelegramBotService// : IDisposable
    {
        private readonly TelegramBotSettings _config;
        private readonly SmartPlugService _smartPlugService;

        private List<long> _notifyIDs;

        public TelegramBotClient Client { get; }

        public TelegramBotService(IOptions<TelegramBotSettings> config, SmartPlugService smartPlugService)
        {
            _notifyIDs = new List<long>();
            _config = config.Value;
            _smartPlugService = smartPlugService;

            if (string.IsNullOrEmpty(_config.BotToken))
                throw new ArgumentNullException(nameof(_config.BotToken));

            Client = new TelegramBotClient(_config.BotToken);
            //Client.SetWebhookAsync("https://1b0dd5af.ngrok.io:8443/api/TelegramBotUpdate").Wait();
        
            _smartPlugService.OnEDeviceRunningChanged += SendNotifications;
        }

        public void AddNotification(long chatId)
        {
            if(!_smartPlugService.EDevice.Running)
            {
                Client.SendTextMessageAsync(chatId, "Die Waschmaschine läuft derzeit nicht.");
                return;
            }
            _notifyIDs.Add(chatId);
            Client.SendTextMessageAsync(chatId, "Du wirst benachrichtigt, sobald die Waschmaschine fertig ist.");
        }

        public void SendStatus(long chatId)
        {
            string text = "Die Waschmaschine ist gerade aus.";
            if (_smartPlugService.EDevice.Running)
                text = "Die Waschmaschine läuft gerade.";
            Client.SendTextMessageAsync(chatId, text);
        }

        public void SendNotifications(EDevice edevice)
        {
            if(!edevice.Running)
            {
                foreach (var chat in _notifyIDs)
                    Client.SendTextMessageAsync(chat, "Die Waschmaschine ist jetzt fertig.");
                _notifyIDs.Clear();
            }
        }

        public void SendPossibleCommands(long chatId)
        {
            string msg = "Die folgenden Kommandos sind möglich:\n"
                        + "/status - Gibt den aktuellen Status der Waschmaschine aus\n"
                        + "/notify - Benachrichtigt dich, sobald die Waschmaschine fertig ist";
            Client.SendTextMessageAsync(chatId, msg);
        }

        public void Dispose()
        {
            //Client.DeleteWebhookAsync().Wait();
            //GC.SuppressFinalize(this);
        }

        ~TelegramBotService()
        {
            //Dispose();
        }
    }
}