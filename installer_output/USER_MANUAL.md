# PANN POS System – Simple User Guide

Use this guide after the program is installed. It explains the daily tasks in plain language so cashiers and store staff can work confidently.

---

## 1. Opening the Cash Register

1. Double-click the desktop shortcut **PANN POS System**.
2. Wait for the black console window to finish loading.
3. Open Google Chrome (or your browser) and go to `http://localhost:8000`.
4. Log in with your username/email and password.
5. On the left menu, click **Shift**.
6. Type the cash you counted in the drawer under **Starting Cash**.
7. Press **Start Shift**. The system now records all sales under this shift.

> **Remember:** Keep the console window open while you work. Closing it stops the POS.

---

## 2. Making a Sale

1. Click **New Order** on the sidebar.
2. Browse categories at the top or use the search box to find items.
3. Click an item to add it to the cart.
   - If you have a barcode scanner, scan the code or type it into **Manual Barcode Entry**, then click **Add Product**.
4. When you’ve added the customer’s items, click the cart badge or choose **Checkout**.

### At the Checkout Screen

1. Review the items. Use the **+/-** buttons to change quantity or the **trash can** to remove an item.
2. (Optional) Search for the customer to apply loyalty points.
3. Choose the payment method:
   - **Cash** – enter the amount received; the system shows change.
   - **Card / PayMongo** – select the right option and confirm once payment is successful.
   - **COD** – for delivery orders paid with cash on delivery.
4. Click **Complete Order**. A receipt appears in the History page, and the cart clears.

---

## 3. Handling Online Orders

1. Click **Online Orders**.
2. Use the tabs to switch between **Pending** and **Complete** orders.
3. Click a pending order to see details.
4. Use the buttons on the right to move the order through stages:
   - **Start Processing** → prepare food or items.
   - **Mark Ready for Delivery** → items are packed or ready for pickup.
   - **Complete** → customer received the order.
   - **Cancel Order** → only if the customer cancels or payment fails.
5. For cash-on-delivery orders, turn on **Cash Received** when the rider brings payment.

---

## 4. Closing the Shift

1. At the end of the day, count the drawer.
2. Go to **Shift**.
3. Enter the amount of cash you counted under **Closing Cash**.
4. Click **Close Shift**. The system:
   - Saves the shift report.
   - Emails the summary to verified managers.
   - Shows the final totals on the right.

> If you see a “Shift Open” warning when starting a new day, someone forgot to close the previous shift. Close it before opening a new one.

---

## 5. Checking Past Sales

### Transaction History
- Click **History**.
- Filter by date, payment method, or status.
- Click **Export CSV** to download transactions if needed.

### Dashboard Overview
- Click **Dashboard** to see today’s revenue, orders, and popular items at a glance.

---

## 6. Updating Your Account

1. Go to **Settings**.
2. Check your profile details (name, username, email, role).
3. To change your password, click **Change Password**, fill out the form, and press **Update**.
4. Switch **Dark Mode** on or off if you prefer a darker or lighter theme.

---

## 7. Email Notifications

Shift reports are emailed to verified managers after closing a shift. If a manager is not receiving emails:
1. Ask an administrator to verify their account (set `email_verified = True`).
2. Confirm the email address is listed in the environment setting `SHIFT_SUMMARY_ADMIN_EMAILS` if required.

---

## 8. Common Questions

| Question | Answer |
| --- | --- |
| The screen shows “Sold Out”. What do I do? | That item has zero stock. Restock it in back office or wait until the next sync. |
| My order won’t complete. | Make sure at least one item is in the cart and a payment method is chosen. |
| Can I go back after completing a sale? | Find the sale in **History** and review the details there. |
| The system says MongoDB is offline. | Call your supervisor or IT support. MongoDB is the database and must be running. |
| Customers aren’t seeing loyalty points. | Ensure you linked the correct customer at checkout and closed the shift afterward. |

---

## 9. Getting Help

- Keep this guide and the installation manual together.
- If the program crashes, take a photo of the console window or error message.
- Contact your supervisor or IT support with the error details.

---

**You are ready to use the PANN POS System!**  
Happy selling!

