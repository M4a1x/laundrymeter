namespace Laundrymeter.Settings
{
    public class SmartPlugSettings
    {
        /// <summary>
        /// The Domain/IP-Address of the SmartPlug.
        /// </summary>
        /// <returns></returns>
        public string Host { get; set; }

        /// <summary>
        /// The Port of the SmartPlug on which to request the Data. Default: 9999
        /// </summary>
        /// <returns></returns>
        public int Port { get; set; }

        /// <summary>
        /// The Threshold value in Watt above which the Device is considered running.
        /// </summary>
        /// <returns></returns>
        public float ThresholdW { get; set; }

        /// <summary>
        /// The Time after which a request to the SmartPlug times out. Minimum is 100ms
        /// </summary>
        /// <returns></returns>
        public int RequestTimeoutms { get; set; }
    }
}