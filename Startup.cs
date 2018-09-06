using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.HttpsPolicy;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

using Microsoft.AspNetCore.Authentication.Cookies;
using Laundrymeter.Settings;
using Laundrymeter.Services;
using Laundrymeter.Hubs;

namespace Laundrymeter
{
    public class Startup
    {
        // TODO: Remove all the cookie policy request things
        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public IConfiguration Configuration { get; }

        // This method gets called by the runtime. Use this method to add services to the container.
        public void ConfigureServices(IServiceCollection services)
        {
            // Configure services for Constructor Dependency Injection
            // Configure Configuration
            services.Configure<LdapSettings>(Configuration.GetSection("LdapSettings"));
            services.Configure<SmartPlugSettings>(Configuration.GetSection("SmartPlugSettings"));
            services.Configure<DataRefreshSettings>(Configuration.GetSection("DataRefreshSettings"));
            services.Configure<TelegramBotSettings>(Configuration.GetSection("TelegramBotSettings"));

            // Add Singletons and Transients
            services.AddTransient<LdapService>();
            services.AddSingleton<SmartPlugService>();
            services.AddSingleton<TelegramBotService>();
            services.AddSingleton<IHostedService, DataRefreshService>();

            // Add MVC Middleware
            services.AddMvc()
                .AddRazorPagesOptions(options => 
                {
                    options.Conventions.AuthorizeFolder("/");
                    options.Conventions.AllowAnonymousToPage("/Account/Login");
                })
                .SetCompatibilityVersion(CompatibilityVersion.Version_2_1);

            // See Official Docs, Cookie Authentication without ASP.NET Core Identity for more options
            // https://docs.microsoft.com/de-de/aspnet/core/security/authentication/cookie?view=aspnetcore-2.1&tabs=aspnetcore2x
            services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
                .AddCookie();

            // From another example. should do the same.
            // services.AddAuthentication(options =>
            //     {
            //         options.DefaultSignInScheme = CookieAuthenticationDefaults.AuthenticationScheme;
            //         options.DefaultAuthenticateScheme = CookieAuthenticationDefaults.AuthenticationScheme;
            //         options.DefaultChallengeScheme = CookieAuthenticationDefaults.AuthenticationScheme;
            //     }).AddCookie(options => { options.LoginPath = "/Account/Login"; });

            // Add SignalR for realtime communication (aka push new data to clients)
            services.AddSignalR();
        }

        // This method gets called by the runtime. Use this method to configure the HTTP request pipeline.
        public void Configure(IApplicationBuilder app, Microsoft.AspNetCore.Hosting.IHostingEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }
            else
            {
                app.UseExceptionHandler("/Error");
                app.UseHsts();
            }

            app.UseHttpsRedirection();
            app.UseStaticFiles();

            // Add Cookie Middleware to handle auth cookies
            app.UseCookiePolicy();

            // Call UseAuthentication() before UseMvc()
            app.UseAuthentication();

            // Use SignalR and configure routes
            app.UseSignalR(routes =>
            {
                routes.MapHub<DataHub>("/datahub");
            });

            app.UseMvc();
        }
    }
}
