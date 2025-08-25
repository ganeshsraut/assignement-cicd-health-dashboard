import nodemailer from "nodemailer";

export async function sendFailureEmail(runInfo) {
  let transporter = nodemailer.createTransport({
    service: "gmail",
    auth: {
      user: process.env.GMAIL_USER,
      pass: process.env.GMAIL_PASS,
    },
  });

  await transporter.sendMail({
    from: `"CI/CD Bot" <${process.env.GMAIL_USER}>`,
    to: "your-email@gmail.com",
    subject: `🚨 CI/CD Failed - ${runInfo.repo}`,
    text: `The pipeline failed.\n\nDetails:\n${JSON.stringify(runInfo, null, 2)}`,
  });
}