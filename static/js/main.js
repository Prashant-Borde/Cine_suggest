let currentIndex = 0;
const slides = document.querySelectorAll('.hero-slider .slide');

function showNextSlide() {
    slides[currentIndex].classList.remove('active');
    currentIndex = (currentIndex + 1) % slides.length; // Loop back to the first slide
    slides[currentIndex].classList.add('active');
}

// Initialize the first slide as active
slides[currentIndex].classList.add('active');

// Change slide every 4 seconds
setInterval(showNextSlide, 4000);
