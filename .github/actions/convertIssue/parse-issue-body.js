import { readFile } from "node:fs/promises";
import yaml from "js-yaml";

function normalizeNewLines(str) {
  return str.replace(/\r\n/g, "\n");
}

function splitList(str){
  let list = str.split(',');
  for(let i = 0; i < list.length; i++) {
    list[i] = list[i].trim();
  }

  if(list.length == 1 && list[0] == ''){
    return [];
  }
  return list;
}

function cleanBoolean(str) {
  if(str === 'true' || str === 'True'){
    return true;
  } else {
    return false;
  }
}

async function parseFields(githubIssueTemplateFile) {
  let issueTemplate = await readFile(githubIssueTemplateFile, "utf8");
  let githubFormData = yaml.load(issueTemplate);

  // Markdown fields aren’t included in output body
  let fields = githubFormData.body.filter(field => field.type !== "markdown");
  console.log("got ", fields.length, " fields", fields);
  return fields;
}

function parseBodyData(body) {
  // Warning: this will likely not handle new lines in a textarea field input
  let bodyData = normalizeNewLines(body).split("\n").filter(entry => {
    return !!entry && !entry.startsWith("###")
  }).map(entry => {
    entry = entry.trim();

    return entry === "_No response_" ? "" : entry;
  });
  console.log("got form body with length ", bodyData.length, bodyData);

  return bodyData;
}

function parseCombined(fields, bodyData) {
  //map fields and entries to an object, then we map that 
  let returnObject = {};
  for(let j = 0, k = bodyData.length; j<k; j++) {
    //skip matching if the field does not exist
    if(!fields[j]) {
      continue;
    }
    let entry = bodyData[j];
    returnObject[fields[j].id] = entry;
  }
  console.log("combined form and body to get", returnObject);
  return returnObject;
}

function getSurveyInfo(dataObject) {
  console.log("constructing survey info");
  let surveyInfo = {};

  //demographics survey settings
  if(dataObject.survey_form_path) {
    surveyInfo.surveys = { 
      UserProfileSurvey: {
        "formPath": "json/demo-survey-v2.json",
        "version": 1,
        "compatibleWith": 1,
        "dataKey": "manual/demographic_survey",
        "labelTemplate": {
          "en": "Answered",
          "es": "Contestada"
        }
      }
    }
  } else {
    surveyInfo.surveys = {
      UserProfileSurvey: {
        "formPath": 'https://raw.githubusercontent.com/e-mission/nrel-openpath-deploy-configs/main/survey_resources/' + dataObject.url_abbreviation + '/' + dataObject.custom_dem_survey_path,
        "version": 1,
        "compatibleWith": 1,
        "dataKey": "manual/demographic_survey",
        "labelTemplate": {
          "en": dataObject.labelTemplate_lang1.split('-')[1].trim(),
          "es": dataObject.labelTemplate_lang2.split('-')[1].trim()
        }
      }
    }
  }

  //labeling options
  if(dataObject.label_form_path){
    surveyInfo['trip-labels'] = "MULTILABEL";
  } else if (dataObject.label_options && dataObject.label_options != '') {
    surveyInfo['trip-labels'] = "MULTILABEL"; //label_options goes outside of this?
  } else {
    //TODO determine proceedure for custom label surveys
    surveyInfo['trip-labels'] = "ENKETO";
  }

  return surveyInfo;
}

function getTextForLanguage(language_key, dataObject) {
  const textKeys = ['deployment_partner_name', 'deployment_name', 'summary_line_1', 
                    'summary_line_2', 'summary_line_3', 'short_textual_description', 
                    'why_we_collect'];
  
  let languageText = {};
  for(let i = 0; i < textKeys.length; i++) {
    languageText[textKeys[i]] = dataObject[textKeys[i] + language_key];
  }

  let researchQuestions = [dataObject['research_question_1' + language_key],
                           dataObject['research_question_2' + language_key],
                           dataObject['research_question_3' + language_key]];

  let blank = true;               
  for(let i = 0; i < researchQuestions.length; i++) {
    if(researchQuestions[i] != "") {
      blank = false;
    }
  }
  if(!blank) {
    languageText.research_questions = researchQuestions;
  } else {
    languageText.research_questions = [];
  }

  return languageText;
}

function getTranslatedText(dataObject) {
  let translatedText = {};
  translatedText[dataObject['lang_1']] = getTextForLanguage('_lang1', dataObject);

  if(dataObject.lang_2 != "None") {
    translatedText[dataObject['lang_2']] = getTextForLanguage('_lang2', dataObject)
  }

  return translatedText;
}

/**
 * TODO: ensure good error messaging so deployers can fix bugs
 * fields are from the issue template
 * bodyData is from the filled out issue
 * @param {*} githubIssueTemplateFile - the issue template that created this request
 * @param {*} body - body of the issue for this request
 * @returns an object for the config file, formatted as existing files in repo are
 */
export async function parseIssueBody(githubIssueTemplateFile, body) {
  //first handle the input, combined object for key/value pairs
  let fields = await parseFields(githubIssueTemplateFile);
  let bodyData = parseBodyData(body);
  let combinedObject = parseCombined(fields, bodyData);

  let configObject = {};
  configObject['url_abbreviation'] = combinedObject.url_abbreviation;
  configObject['version'] = 1;
  configObject['ts'] = Date.now();

  let connect_url = 'https://' + combinedObject.url_abbreviation + '-openpath.nrel.gov/api/';
  configObject['server'] = {connectURL: connect_url, aggregate_call_auth: 'user_only'}; //TODO check options for call + add to form?

  let subgroups = combinedObject.subgroups.split(',');
  configObject['opcode'] = {autogen: cleanBoolean(combinedObject.autogen), subgroups: subgroups};
  
  let textObject = getTranslatedText(combinedObject);
  configObject['intro'] = {
    program_or_study: combinedObject.program_or_study,
    start_month: combinedObject.start.split( '/')[0],
    start_year: combinedObject.start.split('/')[1],
    mode_studied: combinedObject.mode_studied, 
    program_admin_contact: combinedObject.program_admin_contact,
    deployment_partner_name: combinedObject.deployment_partner_name_lang1,
    translated_text: textObject
  };

  configObject['survey_info'] = getSurveyInfo(combinedObject);
  if(combinedObject.label_options) {
    configObject.label_options = 'https://raw.githubusercontent.com/e-mission/nrel-openpath-deploy-configs/main/label_options/' + combinedObject.label_options;
  }
  //TODO: add handling for custom trip surveys

  configObject['display_config'] = { use_imperial: cleanBoolean(combinedObject.use_imperial) };
  configObject['metrics'] = { include_test_users: cleanBoolean(combinedObject.include_test_users) };
  configObject['profile_controls'] = { support_upload: false, trip_end_notification: cleanBoolean(combinedObject.trip_end_notification) };

  configObject['admin_dashboard'] = {
    data_trips_columns_exclude: splitList(combinedObject.data_trips_columns_exclude),
    additional_trip_columns: splitList(combinedObject.additional_trip_columns),
    data_uuids_columns_exclude: splitList(combinedObject.data_uuids_columns_exclude),
    //TODO: will this ever NOT be nrelop?
    token_prefix: "nrelop"
  }

  //list of all the boolean values in the admin dashboard section, add to issue template and list for new value
  let ADMIN_LIST = ['overview_users', 'overview_active_users', 'overview_trips', 'overview_signup_trends', 
                    'overview_trips_trend', 'data_uuids', 'data_trips', 'token_generate', 'map_heatmap', 
                    'map_bubble', 'map_trip_lines', 'options_uuids', 'options_emails'];

  for(let i = 0; i < ADMIN_LIST.length; i++) {
    configObject['admin_dashboard'][ADMIN_LIST[i]] = cleanBoolean(combinedObject[ADMIN_LIST[i]]);
  }

  //TODO: add handling for custom reminder schemes
  
  console.log( configObject );
  return configObject;
}