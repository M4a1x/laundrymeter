using System;
using Novell.Directory.Ldap;
using Microsoft.Extensions.Options;
using Laundrymeter.Settings;

namespace Laundrymeter.Services
{
    public class LdapService
    {
        private readonly LdapSettings _ldapSettings;

        public LdapService(IOptions<LdapSettings> ldapSettingsOptions)
        {
            _ldapSettings = ldapSettingsOptions.Value;

            if (string.IsNullOrEmpty(_ldapSettings.ServerName))
                throw new ArgumentNullException(nameof(_ldapSettings.ServerName));
            if (_ldapSettings.ServerPort < 0 || _ldapSettings.ServerPort > UInt16.MaxValue)
                throw new ArgumentOutOfRangeException($"Port must be between 0 and {UInt16.MaxValue}");
            if (string.IsNullOrEmpty(_ldapSettings.SearchBase))
                throw new ArgumentNullException(nameof(_ldapSettings.SearchBase));
        }

        /// <summary>
        /// Connects to the LDAP Server without binding
        /// </summary>
        /// <returns>The LDAP connection to the server</returns>
        private LdapConnection GetConnection()
        {
            var ldapConnection = new LdapConnection() { SecureSocketLayer = true };
            
            // For now, skip certificate Check
            // TODO: Make certificates work!
            ldapConnection.UserDefinedServerCertValidationDelegate += (s,c,h,e) => true;
            ldapConnection.Connect(this._ldapSettings.ServerName, this._ldapSettings.ServerPort);

            return ldapConnection;
        }

        private string getLoginName(string sAMAccountName)
        {
            // So users just need to enter their login name
            return sAMAccountName + "@" + _ldapSettings.ServerName;
        }

        /// <summary>
        /// Authenticate the user against the ldap database configured in appsettings.json
        /// Tries logging in (bind) with supplied data. If it succeeds the user is valid.
        /// </summary>
        /// <param name="sAMAccountName">Username of the user</param>
        /// <param name="password">Password of the user</param>
        /// <returns>True on success, False otherwise</returns>
        public bool AuthenticateLdap(string sAMAccountName, string password)
        { 
            string loginName = getLoginName(sAMAccountName);

            //Force SSL
            using (var ldapConnection = GetConnection())
            {
                // try logging in with supplied userdata, if it works, it's a valid user
                try
                {
                    ldapConnection.Bind(loginName, password);
                    return true;
                }
                catch (Exception)
                {
                    return false;
                }
            }
        }

        /// <summary>
        /// Logs in with the provided credentials and gets the Email address of the user
        /// </summary>
        /// <param name="sAMAccountName">Username of the user</param>
        /// <param name="password">Password of the user</param>
        /// <returns>The E-Mail address</returns>
        public string getEmail(string sAMAccountName, string password)
        {
            string email = String.Empty;
            string loginName = getLoginName(sAMAccountName);
            var filter = $"(&(objectClass=user)(sAMAccountName={sAMAccountName}))";

            using (var ldapConnection = GetConnection())
            {
                ldapConnection.Bind(loginName, password);
                var search = ldapConnection.Search(
                    _ldapSettings.SearchBase,
                    LdapConnection.SCOPE_SUB,
                    filter,
                    new[] {"mail"},
                    false,
                    null,
                    null);

                LdapMessage message;

                while ((message = search.getResponse()) != null)
                {
                    if (!(message is LdapSearchResult searchResultMessage))
                    {
                        continue;
                    }

                    email = searchResultMessage.Entry.getAttribute("mail")?.StringValue;
                }
            }
            return email;
        }      
    }
}