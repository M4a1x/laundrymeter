using System.ComponentModel.DataAnnotations;
using System.Security.Claims;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

using System;
using System.Threading;
using Laundrymeter.Services;

using Microsoft.AspNetCore.Authentication.Cookies;
using System.Collections.Generic;

namespace Laundrymeter.Pages.Account
{
    public class LoginModel : PageModel
    {
        private readonly LdapService _ldapService;

        [BindProperty]
        public InputModel Input { get; set; }

        public string ReturnUrl { get; private set; }

        [TempData]
        public string ErrorMessage { get; set; }

        public class InputModel
        {
            [Required]
            public string Username { get; set; }

            [Required]
            [DataType(DataType.Password)]
            public string Password { get; set; }
        }

        public LoginModel(LdapService ldapService)
        {
            _ldapService = ldapService;
        }

        public IActionResult OnGet(string returnUrl = null)
        {
            if (User.Identity.IsAuthenticated)
            {
                return RedirectToPage("/Index");
            }

            if (!string.IsNullOrEmpty(ErrorMessage))
            {
                ModelState.AddModelError(string.Empty, ErrorMessage);
            }

            ReturnUrl = returnUrl;
            return Page();
        }

        public async Task<IActionResult> OnPostAsync(string returnUrl = null)
        {
            ReturnUrl = returnUrl;

            if (ModelState.IsValid)
            {
                if (!_ldapService.AuthenticateLdap(Input.Username, Input.Password))
                {
                    ModelState.AddModelError(string.Empty, "Invalid login attempt.");
                    return Page();
                }

                var email = _ldapService.getEmail(Input.Username, Input.Password);

                var claims = new List<Claim>
                {
                    new Claim(ClaimTypes.Name, Input.Username),
                    new Claim(ClaimTypes.Email, email)
                };

                var claimsIdentity = new ClaimsIdentity(
                    claims, CookieAuthenticationDefaults.AuthenticationScheme);

                var claimsPrincipal = new ClaimsPrincipal(claimsIdentity);

                await HttpContext.SignInAsync(
                    CookieAuthenticationDefaults.AuthenticationScheme, 
                    claimsPrincipal);

                Thread.CurrentPrincipal = claimsPrincipal;

                return LocalRedirect(Url.GetLocalUrl(returnUrl));
            }

            // Something failed. Redisplay the form.
            return Page();
        }
    }
}
