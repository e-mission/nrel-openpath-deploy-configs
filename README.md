# Configuration files for current OpenPATH deployments

Publishing them on GitHub allows transparency around how they are configured.
This may not be the long-term solution, but it allows us to make progress over the short/medium term.

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
        "program_admin_name": "K. Shankari",
        "program_admin_email": "k.shankari@nrel.gov",
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
