// Fonction pour ajouter la classe 'visible' lorsqu'un élément entre dans la fenêtre
// Et 'fade-out' quand il sort de la fenêtre
function handleScroll() {
    const timelineItems = document.querySelectorAll('.timeline-item');
  
    // Vérifier la position de chaque item dans la fenêtre
    timelineItems.forEach(item => {
      const rect = item.getBoundingClientRect();
  
      // Lorsque l'élément entre dans la fenêtre, on lui ajoute la classe 'visible'
      if (rect.top <= window.innerHeight && rect.bottom >= 0) {
        item.classList.add('visible');
        item.classList.remove('fade-out');  // On retire fade-out si l'élément est visible
      } else {
        item.classList.remove('visible');
        item.classList.add('fade-out');  // On applique fade-out si l'élément sort
      }
    });
  }

  window.addEventListener('scroll', function() {
    const timelineItems = document.querySelectorAll('.timeline-item');
    timelineItems.forEach(function(item) {
      const position = item.getBoundingClientRect().top;
      if (position < window.innerHeight - 100) {
        item.classList.add('visible');
      } else {
        item.classList.remove('visible');
      }
    });
  });
  