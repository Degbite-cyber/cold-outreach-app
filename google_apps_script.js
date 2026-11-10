function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Leads") || SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);
    var action = data.action;

    // 1. GET ALL LEADS
    if (action === "get_leads") {
      var rows = sheet.getDataRange().getValues();
      var headers = rows[0];
      var result = [];
      for (var i = 1; i < rows.length; i++) {
        var rowObj = { "_row_number": i + 1 };
        for (var j = 0; j < headers.length; j++) {
          rowObj[headers[j]] = rows[i][j];
        }
        result.push(rowObj);
      }
      // Check master pause switch at cell O2
      var pauseVal = sheet.getRange("O2").getValue();
      var isPaused = (pauseVal && pauseVal.toString().trim().toUpperCase() === "PAUSED");

      return ContentService.createTextOutput(JSON.stringify({
        status: "success",
        is_paused: isPaused,
        leads: result
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // 2. UPDATE A SPECIFIC ROW
    if (action === "update_lead") {
      var rowNum = data.row_number;
      var updates = data.updates; // e.g. {email_status: "VALID", draft_subject: "..."}
      var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

      for (var colName in updates) {
        var colIndex = headers.indexOf(colName) + 1;
        if (colIndex > 0) {
          sheet.getRange(rowNum, colIndex).setValue(updates[colName]);
        }
      }

      return ContentService.createTextOutput(JSON.stringify({
        status: "success",
        updated_row: rowNum
      })).setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: "Unknown action"
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
