(function () {
  function closeAll(except) {
    document.querySelectorAll('.ajax-search-results.open').forEach(function (panel) {
      if (panel !== except) panel.classList.remove('open');
    });
  }

  document.querySelectorAll('.ajax-search-select').forEach(function (wrapper) {
    var input = wrapper.querySelector('.ajax-search-input');
    var hidden = wrapper.querySelector('input[type="hidden"]');
    var results = wrapper.querySelector('.ajax-search-results');
    var endpoint = wrapper.dataset.endpoint;
    var timer = null;
    var controller = null;

    function showMessage(message) {
      results.innerHTML = '<div class="ajax-search-message">' + message + '</div>';
      results.classList.add('open');
    }

    function loadResults() {
      var query = input.value.trim();
      hidden.value = '';
      if (!query) {
        results.classList.remove('open');
        results.innerHTML = '';
        return;
      }
      if (controller) controller.abort();
      controller = new AbortController();
      showMessage('Searching...');
      fetch(endpoint + '?q=' + encodeURIComponent(query), {
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        signal: controller.signal
      })
        .then(function (response) {
          if (!response.ok) throw new Error('Search failed');
          return response.json();
        })
        .then(function (payload) {
          results.innerHTML = '';
          var rows = payload.results || [];
          if (!rows.length) {
            showMessage('No matching record found.');
            return;
          }
          rows.forEach(function (row) {
            var button = document.createElement('button');
            button.type = 'button';
            button.className = 'ajax-search-option';
            button.textContent = row.text;
            button.addEventListener('click', function () {
              hidden.value = row.id;
              input.value = row.text;
              results.classList.remove('open');
              results.innerHTML = '';
            });
            results.appendChild(button);
          });
          closeAll(results);
          results.classList.add('open');
        })
        .catch(function (error) {
          if (error.name !== 'AbortError') showMessage('Search could not be loaded. Try again.');
        });
    }

    input.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(loadResults, 250);
    });
    input.addEventListener('focus', function () {
      if (input.value.trim() && !hidden.value) loadResults();
    });
    input.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') results.classList.remove('open');
    });
  });

  document.addEventListener('click', function (event) {
    if (!event.target.closest('.ajax-search-select')) closeAll(null);
  });
})();
