var navbutton = document.getElementById("navbutton");
var sidebar = document.getElementById("mySidebar");
var open = false;

function toggleMenu() {
    if(open == false) {
        sidebar.style.width = "50%";
        open = true;
        navbutton.classList.toggle("change");
    } else {
        sidebar.style.width = "0";
        open = false;
        navbutton.classList.toggle("change");
    }
}

var links = sidebar.getElementById("link");

for (var i = 0; i < links.length; i++) {
    links[i].addEventListener("click", function() {
        var current = document.getElementsByClassName("active");
        current[0].className = current[0].className.replace(" active", "");
        this.className += " active";
    });
}