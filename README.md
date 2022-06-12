# Configuration files for current OpenPATH deployments

Publishing them on GitHub allows transparency around how they are configured.
This may not be the long-term solution, but it allows us to make progress over the short/medium term.

### Reviewing and testing

- If you are here to preview/review/beta test the app functionality, please using the stage environment
- If you are here to test out the app on your personal phone, please using the open-access environment

In general, if you are planning to keep the app installed for less than a day,
please use stage so you don't pollute the real dataset.

### File format

Config format (with default values) is:

```
{
    "version": 1,
    "server": {
        "url": "https://openpath-stage.nrel.gov/api/",
        "aggregate_call_auth": "user_only"
    },
    "intro": {
        "program_or_study": "study",
        "program_admin_contact": "K. Shankari",
        "deployment_partner_name": "National Renewable Energy Laboratory (NREL)",
        "translated_text": {
            "en": {
                "deployment_name": "Open Access Study",
                "summary_line_1": "enables people to track their travel modes and <b>measure</b> their associated energy use and emissions",
                "summary_line_2": "makes <b>aggregated</b> data on mode shares, trip frequencies, and carbon footprints available via a public dashboard",
                "summary_line_3": "serves as a <b>control group</b> while evaluating behavior change of programs.",
                "short_textual_description": "Transportation is the largest contributor to ...",
                "why_we_collect": "NREL can use this information to ....",
            },
            "es": {
....
            },
            "support_autogen_token": true,
        }
    }
    "display_config": {
        "use_imperial": false,
    },
    "profile_controls": {
        "support_upload": false,
        "trip_end_notification": false
    }
}
```

### Development

This repo has some simple GitHub pages in the `docs` repo

If you want to experiment with them (e.g. by changing the format or the URL
prefix), you can use the attached `docker-compose.yml` to serve the pages
locally at http://localhost:9090

I found this useful while testing the QR code functionality on the devapp,
which responds to the `emission` URL prefix, not `nrelopenpath`
