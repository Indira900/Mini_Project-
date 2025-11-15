# TODO: Hide Navigation Items on Login Page

- [x] Modify templates/base.html to conditionally hide navigation items (Dashboard, Predictions, etc.) when user is not logged in, leaving only the "IVF Journey Tracker" brand visible.
- [x] Test the login page to ensure only the brand is shown.
- [x] Verify other pages still show nav items when logged in.

# TODO: Add Success Rate Graph and Update Recent Activity

- [x] Update templates/doctor_dashboard.html to change Recent Activity section to display medical activities (injections, scans, blood work) with appropriate icons and details.
- [x] Update static/js/doctor_dashboard.js to create a bar chart showing success rates for this month vs last month.
- [x] Test the dashboard to ensure the graph displays correctly and recent activities show medical procedures.
- [x] Run the Flask app to test the changes.
