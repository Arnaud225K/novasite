
document.querySelectorAll('.product__images-list div').forEach(thumb => {
    thumb.addEventListener('click', function() {
        const mainImg = document.querySelector('.product__images-image img');
        const newSrc = this.querySelector('img').src;
        
        document.querySelectorAll('.product__images-list div').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        
        mainImg.style.opacity = '0';
        
        setTimeout(() => {
            mainImg.src = newSrc;
            mainImg.style.opacity = '1';
        }, 150);
    });
});

document.querySelector('.product__images-list div:first-child')?.classList.add('active');