*** Settings ***
Library          D:\\ProjectX2\\QAReportLibrary2.py
Library          D:/CIMB_V2/LibraryCustom/XLibrary.py
Library          OperatingSystem
Library          BuiltIn

*** Variables ***
${DATA_FILE}     ${CURDIR}/../DATA/TEST_SUMERY.json
${DEFECTS_FILE}  ${CURDIR}/../DATA/DEFECT.json
${OUTPUT_DIR}    ${CURDIR}/../Report
${MODULAR_TEMPLATE}  ${CURDIR}/../TEMPLATES/base.html
${SUMMARY_TEMPLATE}  ${CURDIR}/../TEMPLATES/partials/test_summary.html
${summary_overall_progress}  ${CURDIR}/../TEMPLATES/partials/summary_overall_progress.html
${summary_test_coverage}  ${CURDIR}/../TEMPLATES/partials/summary_test_coverage.html
${summary_defect_density}  ${CURDIR}/../TEMPLATES/partials/summary_defect_density.html
${summary_time_to_fix}  ${CURDIR}/../TEMPLATES/partials/summary_time_to_fix.html
${test_trend_analysis}  ${CURDIR}/../TEMPLATES/partials/test_trend_analysis.html



*** Test Cases ***
Generate QA Report Test (Modular Template)
    [Setup]    Setup Test Environment
    Setup QA Report    ${DATA_FILE}    ${MODULAR_TEMPLATE}    ${OUTPUT_DIR}    ${DEFECTS_FILE}
    # Prepare Report Data
    Prepare Test Summary Data 
    Prepare Defect Trend Analysis Data
    Prepare Test Trend Analysis Data
    Prepare Module Testing Status Data
    Prepare Defect Distribution Data
    Prepare Defect Resolution Time Data
    Prepare Recent Defects Data
    # ${DATA_TEST}    Load Test Data
    # XLog tree data    ${DATA_TEST}
    Generate QA Report
    # Find Key Html Report    ${SUMMARY_TEMPLATE}
    # Check Template Key Exists    ${SUMMARY_TEMPLATE}    PROJECT_NAME

    Get Template Keys With Value    ${SUMMARY_TEMPLATE}
    Get Template Keys With Value    ${summary_overall_progress}
    Get Template Keys With Value    ${summary_test_coverage}
    Get Template Keys With Value    ${summary_defect_density}
    Get Template Keys With Value    ${summary_time_to_fix}
    Get Template Keys With Value    ${test_trend_analysis}


*** Keywords ***
Setup Test Environment
    Create Directory    ${OUTPUT_DIR}
    File Should Exist    ${DATA_FILE}    msg=Data file not found: ${DATA_FILE}
    File Should Exist    ${DEFECTS_FILE}    msg=Defects file not found: ${DEFECTS_FILE}
    File Should Exist    ${MODULAR_TEMPLATE}    msg=Template file not found: ${MODULAR_TEMPLATE}

Cleanup Test Environment
    Clear QA Report Cache
    Remove Directory    ${OUTPUT_DIR}    recursive=True


