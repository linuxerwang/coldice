function search_keywords(p) {
  if (p == undefined) {
    p = 1;
  }
  $('#results_box').html('Searching ...')
  $('#results_box').load('/s?q='+encodeURI($("#input_search").val()+'&p='+p),
    function(response, status, xhr) {
      header = []

      if (xhr.getResponseHeader('Search-Size')) {
        header.push(xhr.getResponseHeader('Search-Size'));
        header.push(' results.');
      }
      if (xhr.getResponseHeader('Search-Pages')) {
        header.push(' Page ');
        header.push(xhr.getResponseHeader('Search-Page'));
        header.push(' of ');
        header.push(xhr.getResponseHeader('Search-Pages'));
        header.push('.');
      }
      if (xhr.getResponseHeader('Search-Prev')) {
        header.push(' <a class="navlink" href="#" onclick="return search_keywords(');
        header.push(xhr.getResponseHeader('Search-Prev'));
        header.push(');">Prev</a>');
      }
      if (xhr.getResponseHeader('Search-Next')) {
        header.push(' <a class="navlink" href="#" onclick="return search_keywords(');
        header.push(xhr.getResponseHeader('Search-Next'));
        header.push(');">Next</a>');
      }

      $('#result_header').html(header.join(''));
    }
  );
  return false;
}

$(document).ready(function() {
  $("#input_search").bind("keypress", function(e) {
    if (e.keyCode == 13) {
      search_keywords();
      return false;
    }
  });
  $("#btn_search").click(function() {
    search_keywords();
  });
});

