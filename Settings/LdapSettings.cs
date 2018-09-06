namespace Laundrymeter.Settings
{
    public class LdapSettings
    {
        /// <summary>
        /// Address of the LDAP server. Also used to generate the sAMAdress.
        /// </summary>
        /// <returns></returns>
        public string ServerName { get; set; }

        /// <summary>
        /// The Port the LDAP server is running on.
        /// </summary>
        /// <returns></returns>
        public int ServerPort { get; set; }

        /// <summary>
        /// The base in which all search operations should be performed.
        /// </summary>
        /// <returns></returns>
        public string SearchBase { get; set; }
    }
}