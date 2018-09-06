using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Options;

using Laundrymeter.Settings;

namespace Laundrymeter.Services
{
    public class DataRefreshService : BackgroundService
    {
        private readonly SmartPlugService _smartPlugService;
        private readonly DataRefreshSettings _dataRefreshSettings;

        public DataRefreshService(
            SmartPlugService smartPlugService,
            IOptions<DataRefreshSettings> dataRefreshSettingsOptions)
        {
            _smartPlugService = smartPlugService;
            _dataRefreshSettings = dataRefreshSettingsOptions.Value;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            while (!stoppingToken.IsCancellationRequested)
            {
                await _smartPlugService.UpdateEDevice(stoppingToken);
                await Task.Delay(_dataRefreshSettings.RefreshIntervalms, stoppingToken);
            }
        }
    }
}