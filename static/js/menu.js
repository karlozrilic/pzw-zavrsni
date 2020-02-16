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