using System;
using System.Collections;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using System.Linq;
using Telegram.Bot.Types;
using Telegram.Bot;
using Telegram.Bot.Types.Enums;
using Laundrymeter.Services;

namespace Laundrymeter.Controllers
{
    [Route("api/[controller]/[action]")]
    public class TelegramBotController : Controller
    {
        private readonly TelegramBotService _telegramService;

        public TelegramBotController(TelegramBotService telegramService)
        {
            _telegramService = telegramService;
        }

        // POST api/telegrambotupdate
        // TODO change to api/TelegramBot/Update when moving from scoped to singleton
        [HttpPost]
        public IActionResult Update([FromBody]Update update)
        {
            if (update.Type != UpdateType.Message && update.Message.Type != MessageType.Text)
                return Ok();

            if(update.Message.Entities == null)
            {
                _telegramService.Client.SendTextMessageAsync(update.Message.Chat.Id, "Deine Nachricht muss ein Kommando enthalten.");
                _telegramService.SendPossibleCommands(update.Message.Chat.Id);
                return Ok();
            }

            // Methoden irgendwie als Async kennzeichnen?
            if (update.Message.Entities.Any(entity => entity.Type == MessageEntityType.BotCommand))
            {
                if(update.Message.EntityValues.Any(cmd => cmd == "/start"))
                {

                    string[] words = update.Message.Text.Split(" ",StringSplitOptions.RemoveEmptyEntries);
                    int index = Array.FindIndex(words, element => element == "/start");
                    if(words.Length > index + 1 && words[index+1] == "notify")
                        _telegramService.AddNotification(update.Message.Chat.Id);

                    _telegramService.SendPossibleCommands(update.Message.Chat.Id);
                }

                if(update.Message.EntityValues.Any(cmd => cmd == "/status"))
                    _telegramService.SendStatus(update.Message.Chat.Id);

                if(update.Message.EntityValues.Any(cmd => cmd == "/notify"))
                    _telegramService.AddNotification(update.Message.Chat.Id);
            }

            return Ok();
        }
}
}