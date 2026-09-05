from jinja2 import Template

VERIFICATION_TEMPLATE: Template = Template(
"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verify your email</title>
</head>
<body style="margin:0; padding:0; background-color:#0a0a0a; font-family:'Segoe UI', system-ui, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0a0a0a; padding:40px 20px;">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background-color:#1a1a1a; border:1px solid rgba(0,212,255,0.30); border-radius:16px; overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="padding:32px 40px; text-align:center; border-bottom:1px solid rgba(0,212,255,0.20);">
              <span style="color:#00d4ff; font-size:13px; font-weight:700; letter-spacing:2.8px; text-transform:uppercase;">Nexus Writer</span>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <h1 style="margin:0 0 16px; font-size:20px; font-weight:700; color:#ffffff; letter-spacing:0.5px;">Verify your email address</h1>
              <p style="margin:0 0 32px; font-size:15px; line-height:1.6; color:#b3b3b3;">
                Click the button below to verify your email and activate your account. This link expires in {{expires_in_minutes}} minutes.
              </p>

              <!-- Button -->
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 32px;">
                <tr>
                  <td style="background-color:#00d4ff; border-radius:8px;">
                    <a href="{{verification_url}}" target="_blank" style="display:inline-block; padding:14px 32px; color:#0a0a0a; font-size:14px; font-weight:700; text-decoration:none; letter-spacing:1.4px; text-transform:uppercase;">
                      Verify Email
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 12px; font-size:12px; line-height:1.5; color:#666666; letter-spacing:0.5px;">
                If the button doesn't work, copy and paste this link into your browser:
              </p>
              <p style="margin:0 0 32px; font-size:12px; line-height:1.5; color:#00d4ff; word-break:break-all;">
                {{verification_url}}
              </p>

              <hr style="border:none; border-top:1px solid rgba(0,212,255,0.20); margin:0 0 24px;">

              <p style="margin:0; font-size:12px; line-height:1.5; color:#666666;">
                If you didn't create an account with Nexus Writer, you can safely ignore this email.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
)

RESET_TEMPLATE: Template = Template(
"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset your password</title>
</head>
<body style="margin:0; padding:0; background-color:#0a0a0a; font-family:'Segoe UI', system-ui, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0a0a0a; padding:40px 20px;">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background-color:#1a1a1a; border:1px solid rgba(0,212,255,0.30); border-radius:16px; overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="padding:32px 40px; text-align:center; border-bottom:1px solid rgba(0,212,255,0.20);">
              <span style="color:#00d4ff; font-size:13px; font-weight:700; letter-spacing:2.8px; text-transform:uppercase;">Nexus Writer</span>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <h1 style="margin:0 0 16px; font-size:20px; font-weight:700; color:#ffffff; letter-spacing:0.5px;">Reset your password</h1>
              <p style="margin:0 0 32px; font-size:15px; line-height:1.6; color:#b3b3b3;">
                We received a request to reset the password for your account. Click the button below to choose a new password. This link expires in {{expires_in_minutes}} minutes.
              </p>

              <!-- Button -->
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 32px;">
                <tr>
                  <td style="background-color:#00d4ff; border-radius:8px;">
                    <a href="{{reset_url}}" target="_blank" style="display:inline-block; padding:14px 32px; color:#0a0a0a; font-size:14px; font-weight:700; text-decoration:none; letter-spacing:1.4px; text-transform:uppercase;">
                      Reset Password
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 12px; font-size:12px; line-height:1.5; color:#666666; letter-spacing:0.5px;">
                If the button doesn't work, copy and paste this link into your browser:
              </p>
              <p style="margin:0 0 32px; font-size:12px; line-height:1.5; color:#00d4ff; word-break:break-all;">
                {{reset_url}}
              </p>

              <hr style="border:none; border-top:1px solid rgba(0,212,255,0.20); margin:0 0 24px;">

              <p style="margin:0; font-size:12px; line-height:1.5; color:#666666;">
                If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
)