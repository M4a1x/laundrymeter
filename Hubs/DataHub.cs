using Microsoft.AspNetCore.SignalR;
using System.Threading.Tasks;

using Laundrymeter.Services;

namespace Laundrymeter.Hubs
{
    // Contains functions the clients can call on the server
    public class DataHub : Hub
    {
        // public async Task<bool> RegisterEmail(string email)
        // {
        //     // TODO: Implement a email notification service. Probably as form though.
        //     return true;
        // }
    }
}