using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Claims;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.AspNetCore.SignalR;
using Newtonsoft.Json;

using Laundrymeter.Hubs;
using Laundrymeter.Services;

namespace Laundrymeter.Pages
{
    public class IndexModel : PageModel
    {
        private readonly SmartPlugService _smartPlugService;
        private readonly IHubContext<DataHub> _dataHub;

        public EDevice EDevice { get; private set; }

        public string Email { get; private set; }

        public IndexModel(SmartPlugService smartPlugService, IHubContext<DataHub> datahub)
        {
            _smartPlugService = smartPlugService;
            _dataHub = datahub;

            _smartPlugService.OnEDeviceChanged += updateClient;
        }

        // Initial request of the Data
        public void OnGet()
        {
            EDevice = _smartPlugService.EDevice;
            Email = User.Identity.GetEmail();
        }

        // Update the Data whenever it has been updated (eventDriven)
        private async void updateClient(EDevice edevice)
        {
            await _dataHub.Clients.All.SendAsync("DisplayData", JsonConvert.SerializeObject(edevice));
        }
    }
}
