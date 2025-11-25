
    document.addeventlistener('domcontentloaded', function() {
    const dropdowncontainer = document.queryselector('.price-dropdown-container');
    const dropdowntrigger = document.queryselector('.price-dropdown-trigger');

    dropdowntrigger.addeventlistener('click', function(event) {
        event.stoppropagation();
        dropdowncontainer.classlist.toggle('active');
    });

    window.addeventlistener('click', function(event) {
        if (dropdowncontainer.classlist.contains('active') && !dropdowncontainer.contains(event.target)) {
            dropdowncontainer.classlist.remove('active');
        } 
});
    });