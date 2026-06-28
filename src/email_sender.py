import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_weekly_email(papers, sender_email, sender_password, receiver_email):
    """
    Formats the accumulated papers into an HTML email and sends it.
    """

    if not all([sender_email, sender_password, receiver_email]):
        print("Email credentials missing. Skipping email notification.")
        print("Ensure SENDER_EMAIL, SENDER_PASSWORD, and RECEIVER_EMAIL are set.")
        return False

    print(f"Preparing to send weekly summary of {len(papers)} papers...")

    # Set up the email container
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Weekly Quant Research Summary ({len(papers)} Strategies Found)"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Construct the HTML body
    html_content = """
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>Your Weekly Quant Strategy Report</h2>
        <p>The automated pipeline has identified <b>{}</b> actionable research papers this week.</p>
        <hr>
    """.format(len(papers))

    for idx, paper in enumerate(papers, 1):
        analysis = paper.get('deep_analysis', {})
        html_content += f"""
        <div style="margin-bottom: 25px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 5px; background-color: #f9f9f9;">
            <h3 style="margin-top: 0; color: #2c3e50;">[{idx}] <a href="{paper['link']}" style="color: #2980b9; text-decoration: none;">{paper['title']}</a></h3>
            <p style="margin: 5px 0;"><strong>Published:</strong> {paper['published'][:10]}</p>
            <p style="margin: 5px 0;"><strong>Target Asset Class:</strong> {analysis.get('asset_class', 'N/A')}</p>
            <p style="margin: 5px 0;"><strong>Claimed Performance:</strong> <span style="color: #27ae60;">{analysis.get('claimed_performance', 'N/A')}</span></p>
            <p style="margin: 5px 0;"><strong>Implementation Difficulty:</strong> {analysis.get('implementation_difficulty', 'N/A')}</p>
            
            <h4 style="margin-bottom: 5px; color: #34495e;">The Core Alpha</h4>
            <p style="margin-top: 5px; line-height: 1.4;">{analysis.get('core_alpha', 'N/A')}</p>
            
            <h4 style="margin-bottom: 5px; color: #34495e;">Executive Summary</h4>
            <p style="margin-top: 5px; font-style: italic; color: #555;">{analysis.get('executive_summary', 'N/A')}</p>
        </div>
        """

    html_content += """
        <p style="font-size: 0.9em; color: #7f8c8d;">Generated automatically by your Quant Research Pipeline.</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_content, 'html'))

    # Send the email via standard SMTP (Defaulting to Gmail's SMTP server)
    try:
        # If using Gmail, you MUST use an "App Password", not your normal login password.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Weekly email successfully sent!")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False