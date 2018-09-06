using System;
using Newtonsoft.Json;

using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Net.Sockets;

using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Options;

using Laundrymeter.Settings;

namespace Laundrymeter.Services
{
    public class EMeter
    {
        public EMeter(float voltage, float current, float power, float totalPower)
        {
            Voltage = voltage;
            Current = current;
            Power = power;
            TotalPower = totalPower;
        }

        public float Voltage;
        public float Current;
        public float Power;
        public float TotalPower;
    }

    public class EDevice : EMeter
    {
        private float _threshold;

        public EDevice(float voltage, float current, float power, float totalPower, float threshold)
            : base(voltage, current, power, totalPower)
        {
            _threshold = threshold;
        }

        public bool Running 
        {
            get { return Power > _threshold; }
        }
    }

    public class SmartPlugService
    {
        private readonly SmartPlugSettings _smartPlugSettings;

        /// <summary>
        /// Fires when the E-Meter values have been updated
        /// </summary>
        public event Action<EDevice> OnEDeviceChanged;

        public event Action<EDevice> OnEDeviceRunningChanged;

        /// <summary>
        /// Fires when there is an exception while running the EMeter
        /// </summary>
        public event Action<EDevice, Exception> OnEDeviceException;

        /// <summary>
        /// Contains the last read values of the E-Meter
        /// </summary>
        public EDevice EDevice { get; private set; }

        public SmartPlugService(IOptions<SmartPlugSettings> smartPlugSettingsOptions)
        {
            _smartPlugSettings = smartPlugSettingsOptions.Value;

            if (string.IsNullOrEmpty(_smartPlugSettings.Host))
                throw new ArgumentNullException(nameof(_smartPlugSettings.Host));
            if (_smartPlugSettings.Port < 0 || _smartPlugSettings.Port > UInt16.MaxValue)
                throw new ArgumentOutOfRangeException($"Port must be between 0 and {UInt16.MaxValue}");
            if (_smartPlugSettings.ThresholdW <= 0)
                throw new ArgumentOutOfRangeException("Threshold must be above 0W!");
            if (_smartPlugSettings.RequestTimeoutms < 100)
                throw new ArgumentOutOfRangeException("The Timeout must be at least 100ms!");

            EDevice = new EDevice(-1,-1,-1,-1,_smartPlugSettings.ThresholdW);
        }

        /// <summary>
        /// Update the E-Meter value of the service
        /// </summary>
        /// <param name="stoppingToken">Pass to stop the async Job</param>
        public async Task UpdateEDevice(CancellationToken stoppingToken)
        {
            try
            {
                bool status = EDevice.Running;
                await GetEDeviceRealtime(stoppingToken);
                OnEDeviceChanged?.Invoke(EDevice);
                if (status != EDevice.Running)
                    OnEDeviceRunningChanged?.Invoke(EDevice);
            }
            catch (Exception any)
            {
                // BeginInvoke throws "PlatformNotSupportedException"
                OnEDeviceException?.Invoke(EDevice, any);
            }
        }

        // RefreshInterval is currently also used as timeout. 
        // Maximum time between two requests is therefore 2 * RefreshInterval, in case of Timeout
        /// <summary>
        /// Directly queries the E-Meter for realtime Data of Voltage, Current, Power and PowerTotal
        /// </summary>
        /// <returns>Current E-Meter Values</returns>
        private async Task GetEDeviceRealtime(CancellationToken stoppingToken)
        {
            string cmd = JsonConvert.SerializeObject(new { emeter = new { get_realtime = new { } } });
            byte[] requestCmd = smartPlugEncrypt(cmd);

            using (TcpClient tcpClient = new TcpClient())
            {
                // Config
                tcpClient.NoDelay = true;
                tcpClient.ReceiveTimeout = _smartPlugSettings.RequestTimeoutms;
                tcpClient.SendTimeout = _smartPlugSettings.RequestTimeoutms;

                // Connect
                var tcpConnectTask = tcpClient.ConnectAsync(_smartPlugSettings.Host, _smartPlugSettings.Port);
                await Task.WhenAny(tcpConnectTask, Task.Delay(_smartPlugSettings.RequestTimeoutms)).ConfigureAwait(false);
                if (!tcpConnectTask.IsCompleted)
                {
                    throw new TimeoutException();
                }
                var stream = tcpClient.GetStream();
                stoppingToken.Register(() => stream.Close()); // So the stream get's closed on shutdown of the app. Called by Backgroundservice subclass
                
                // Send
                await stream.WriteAsync(requestCmd, 0, requestCmd.Length).ConfigureAwait(false);

                //Thread.Sleep(100);

                // Needed because the Sockets don't timeout by themselves...
                // see https://github.com/dotnet/corefx/issues/15033
                // from https://stackoverflow.com/questions/12421989/networkstream-readasync-with-a-cancellation-token-never-cancels
                
                // Wait for the response
                // Read header
                byte[] responseHeader = new byte[4];
                var tcpReceiveResultTask = stream.ReadAsync(responseHeader, 0, 4, stoppingToken);
                await Task.WhenAny(tcpReceiveResultTask, Task.Delay(_smartPlugSettings.RequestTimeoutms)).ConfigureAwait(false);

                if (!tcpReceiveResultTask.IsCompleted)
                {
                    throw new TimeoutException();
                }

                if(tcpReceiveResultTask.Result < 4)
                {
                    throw new Exception("The stream was closed by remote party");
                }
                tcpReceiveResultTask = null;

                // Read body
                int responseBodyLength = (responseHeader[0] << 24) + (responseHeader[1] << 16) + (responseHeader[2] << 8) + responseHeader[3];
                byte[] responseBody = new byte[responseBodyLength];
                tcpReceiveResultTask = stream.ReadAsync(responseBody, 0, responseBodyLength, stoppingToken);
                await Task.WhenAny(tcpReceiveResultTask, Task.Delay(_smartPlugSettings.RequestTimeoutms)).ConfigureAwait(false);
                
                if (!tcpReceiveResultTask.IsCompleted)
                {
                    throw new TimeoutException();
                }

                if(tcpReceiveResultTask.Result < responseBodyLength)
                {
                    throw new Exception("The stream was closed by remote party");
                }

                string response = smartPlugDecrypt(responseBody);
                parseEMeterJson(response);
            }
        }

        private byte[] smartPlugEncrypt(string cmd)
        {
            byte[] payload = Encoding.UTF8.GetBytes(cmd);

            byte key = 171;
            byte[] header = getHeader(payload.Length);
            byte[] result = new byte[header.Length + payload.Length];
            Array.Copy(header, result, header.Length);
            for (int j = 4, i = 0; j < result.Length && i < payload.Length; j++, i++)
            {
                byte p = payload[i];
                byte a = (byte)(key ^ p);
                key = a;
                result[j] = a;
            }

            return result;
        }

        private string smartPlugDecrypt(byte[] payload)
        {
            byte key = 171;
            byte[] result = new byte[payload.Length];
            for (int i = 0; i < payload.Length; i++)
            {
                byte p = payload[i];
                byte a = (byte)(key ^ p);
                key = p;
                result[i] = a;
            }

            return Encoding.UTF8.GetString(result);
        }

        private void parseEMeterJson(string json)
        {
            var prototype = new
            {
                emeter = new
                {
                    get_realtime = new
                    {
                        current_ma = 0.0f,
                        voltage_mv = 0.0f,
                        power_mw = 0.0f,
                        total_wh = 0.0f,
                        err_code = 0,
                        err_msg = ""
                    }
                }
            };

            var result = JsonConvert.DeserializeAnonymousType(json, prototype);

            EDevice.Voltage = result.emeter.get_realtime.voltage_mv/1000;
            EDevice.Current = result.emeter.get_realtime.current_ma/1000;
            EDevice.Power = result.emeter.get_realtime.power_mw/1000;
            EDevice.TotalPower = result.emeter.get_realtime.total_wh/1000;
        }

        private byte[] getHeader(int messageLength)
        {
            byte[] header = new byte[4];

            header[0] = (byte)(messageLength >> 24);
            header[1] = (byte)(messageLength >> 16);
            header[2] = (byte)(messageLength >> 8);
            header[3] = (byte)(messageLength);

            return header;
        }
    }
}