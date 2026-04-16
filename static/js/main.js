/**
 * WNACG Gallery - Main JavaScript
 */

// Lazy loading observer
const lazyObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            if (img.dataset.src) {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
            }
            lazyObserver.unobserve(img);
        }
    });
}, {
    rootMargin: '100px',
    threshold: 0.01
});

// Initialize lazy loading for images
function initLazyLoading() {
    document.querySelectorAll('img[data-src]').forEach(img => {
        lazyObserver.observe(img);
    });
}

// Fetch albums and render grid
let currentSort = 'aid_desc';  // 預設排序

async function loadAlbums(sort = 'aid_desc') {
    const grid = document.getElementById('albumGrid');
    const countEl = document.getElementById('albumCount');
    if (!grid) return;

    grid.innerHTML = '<div class="loading">Loading albums</div>';

    try {
        const response = await fetch(`/api/albums?sort=${sort}`);
        const albums = await response.json();

        if (albums.length === 0) {
            grid.innerHTML = '<div class="empty">No albums found</div>';
            if (countEl) countEl.textContent = '0 albums';
            return;
        }

        // 更新總數
        if (countEl) {
            countEl.textContent = `${albums.length} albums`;
        }

        grid.innerHTML = '';
        albums.forEach((album, index) => {
            const card = document.createElement('a');
            card.className = 'album-card';
            card.href = `/album/${encodeURIComponent(album.name)}`;
            card.id = `album-${index}`;  // 唯一 ID
            card.style.animationDelay = `${index * 0.05}s`;
            
            // 點擊時保存位置
            card.addEventListener('click', (e) => {
                saveScrollPosition(index);
            });
            
            card.innerHTML = `
                <img data-src="${album.cover}" alt="${album.name}" loading="lazy">
                <div class="info">
                    <div class="title" title="${album.name}">${album.name}</div>
                    <div class="count">${album.count} images</div>
                </div>
            `;
            grid.appendChild(card);
        });

        initLazyLoading();
        
        // 恢復之前的瀏覽位置
        restoreScrollPosition();
    } catch (error) {
        console.error('Failed to load albums:', error);
        grid.innerHTML = '<div class="empty">Failed to load albums</div>';
        if (countEl) countEl.textContent = '0 albums';
    }
}

// 保存當前滾動位置和最後點擊的 album
function saveScrollPosition(albumIndex) {
    sessionStorage.setItem('galleryScrollY', window.scrollY);
    sessionStorage.setItem('galleryLastAlbum', albumIndex);
}

// 恢復滾動位置和高亮 album
function restoreScrollPosition() {
    const lastAlbumIndex = sessionStorage.getItem('galleryLastAlbum');
    const scrollY = sessionStorage.getItem('galleryScrollY');
    
    if (lastAlbumIndex !== null) {
        const albumCard = document.getElementById(`album-${lastAlbumIndex}`);
        if (albumCard) {
            // 高亮 album（添加動畫效果）
            albumCard.classList.add('highlight');
            setTimeout(() => albumCard.classList.remove('highlight'), 2000);
            
            // 滾動到 album 位置（稍微偏移讓它在視野中間）
            const offset = 100;
            const targetY = albumCard.offsetTop - offset;
            window.scrollTo({ top: targetY, behavior: 'smooth' });
        }
        // 清除記錄
        sessionStorage.removeItem('galleryLastAlbum');
        sessionStorage.removeItem('galleryScrollY');
    } else if (scrollY !== null) {
        // 如果只有滾動位置，直接恢復
        window.scrollTo({ top: parseInt(scrollY), behavior: 'auto' });
        sessionStorage.removeItem('galleryScrollY');
    }
}

// Load album images with infinite scroll
let allImages = [];
let displayedImages = 0;
const IMAGES_PER_LOAD = 20;  // 每次加載的圖片數
let isLoading = false;

async function loadAlbumImages(albumName) {
    const grid = document.getElementById('imageGrid');
    const header = document.getElementById('albumHeader');
    const countEl = document.getElementById('imageCount');
    const loadingIndicator = document.getElementById('loadingIndicator');
    
    if (!grid) return;

    grid.innerHTML = '<div class="loading">Loading images</div>';

    try {
        const response = await fetch(`/api/albums/${encodeURIComponent(albumName)}/images`);
        const data = await response.json();

        if (data.error) {
            grid.innerHTML = '<div class="empty">Album not found</div>';
            if (countEl) countEl.textContent = '0 images';
            return;
        }

        if (header) {
            header.querySelector('h2').textContent = data.album;
        }
        
        // 保存所有圖片
        allImages = data.images.map((img, index) => ({
            src: `/images/${encodeURIComponent(albumName)}/${encodeURIComponent(img)}`,
            filename: img,
            index: index
        }));
        
        displayedImages = 0;
        
        if (countEl) {
            countEl.textContent = `${allImages.length} images`;
        }

        grid.innerHTML = '';
        
        // 加載第一批圖片
        loadMoreImages();
        
        // 設置無限滾動監聽
        setupInfiniteScroll(loadingIndicator);
        
    } catch (error) {
        console.error('Failed to load images:', error);
        grid.innerHTML = '<div class="empty">Failed to load images</div>';
        if (countEl) countEl.textContent = '0 images';
    }
}

// 加載更多圖片
function loadMoreImages() {
    if (isLoading || displayedImages >= allImages.length) return;
    
    isLoading = true;
    const grid = document.getElementById('imageGrid');
    const endIndex = Math.min(displayedImages + IMAGES_PER_LOAD, allImages.length);
    
    for (let i = displayedImages; i < endIndex; i++) {
        const imgData = allImages[i];
        const item = document.createElement('div');
        item.className = 'image-item';
        
        const img = document.createElement('img');
        img.dataset.src = imgData.src;
        img.alt = imgData.filename;
        img.loading = 'lazy';
        
        item.appendChild(img);
        item.addEventListener('click', () => openLightbox(allImages, i));
        
        grid.appendChild(item);
    }
    
    displayedImages = endIndex;
    isLoading = false;
    
    // 重新初始化 lazy loading
    initLazyLoading();
    
    // 如果還有更多圖片，顯示加載指示器
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (displayedImages < allImages.length && loadingIndicator) {
        loadingIndicator.style.display = 'flex';
    } else if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
}

// 設置無限滾動
function setupInfiniteScroll(loadingIndicator) {
    const scrollThreshold = 300;  // 距離底部多少像素時加載
    
    window.addEventListener('scroll', () => {
        const scrollTop = window.scrollY;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        
        // 當接近底部時加載更多
        if (scrollTop + windowHeight >= documentHeight - scrollThreshold) {
            if (!isLoading && displayedImages < allImages.length) {
                loadMoreImages();
            }
        }
        
        // 顯示/隱藏返回按鈕
        const backBtn = document.getElementById('floatingBack');
        if (backBtn) {
            if (scrollTop > 200) {
                backBtn.classList.add('visible');
            } else {
                backBtn.classList.remove('visible');
            }
        }
    });
}

// Lightbox functionality
let currentImages = [];
let currentIndex = 0;

function openLightbox(images, index) {
    // 支持舊格式（albumName）和新格式（圖片對象數組）
    if (typeof images[0] === 'string') {
        // 舊格式：images 是字符串數組，需要 albumName
        const albumName = arguments[2];
        currentImages = images.map(img => `/images/${encodeURIComponent(albumName)}/${encodeURIComponent(img)}`);
    } else {
        // 新格式：images 是對象數組
        currentImages = images.map(img => img.src);
    }
    currentIndex = index;
    
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightboxImg');
    
    lightbox.classList.add('active');
    updateLightboxImage();
    
    document.body.style.overflow = 'hidden';
}

function closeLightbox() {
    const lightbox = document.getElementById('lightbox');
    lightbox.classList.remove('active');
    document.body.style.overflow = '';
}

function updateLightboxImage() {
    const lightboxImg = document.getElementById('lightboxImg');
    lightboxImg.src = currentImages[currentIndex];
}

function prevImage() {
    if (currentIndex > 0) {
        currentIndex--;
        updateLightboxImage();
    }
}

function nextImage() {
    if (currentIndex < currentImages.length - 1) {
        currentIndex++;
        updateLightboxImage();
    }
}

// Keyboard navigation
function handleKeyboard(e) {
    const lightbox = document.getElementById('lightbox');
    if (!lightbox || !lightbox.classList.contains('active')) return;
    
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') prevImage();
    if (e.key === 'ArrowRight') nextImage();
}

// Setup lightbox click zones
function setupLightboxZones() {
    const lightbox = document.getElementById('lightbox');
    if (!lightbox) return;
    
    // 點擊背景關閉
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox || e.target.id === 'lightboxImg') {
            closeLightbox();
        }
    });
    
    // 左側區域 - 上一張
    const leftZone = document.getElementById('leftZone');
    if (leftZone) {
        leftZone.addEventListener('click', (e) => {
            e.stopPropagation();  // 防止觸發背景關閉
            prevImage();
        });
    }
    
    // 右側區域 - 下一張
    const rightZone = document.getElementById('rightZone');
    if (rightZone) {
        rightZone.addEventListener('click', (e) => {
            e.stopPropagation();  // 防止觸發背景關閉
            nextImage();
        });
    }
    
    // 關閉按鈕
    document.getElementById('closeBtn')?.addEventListener('click', (e) => {
        e.stopPropagation();
        closeLightbox();
    });
    
    // 鍵盤導航
    document.addEventListener('keydown', handleKeyboard);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the index page
    if (document.getElementById('albumGrid')) {
        // 從 localStorage 讀取上次選擇的排序
        const savedSort = localStorage.getItem('gallerySort') || 'aid_desc';
        currentSort = savedSort;
        
        // 設置 dropdown 的值
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.value = savedSort;
            
            // 監聽排序變化
            sortSelect.addEventListener('change', (e) => {
                currentSort = e.target.value;
                localStorage.setItem('gallerySort', currentSort);  // 保存選擇
                loadAlbums(currentSort);
            });
        }
        
        loadAlbums(currentSort);
        
        // Setup back to top button
        setupBackToTop();
    }
    
    // Check if we're on the album page
    const albumName = document.getElementById('albumName');
    if (albumName) {
        loadAlbumImages(albumName.dataset.album);
    }
    
    // Setup lightbox event listeners
    const lightbox = document.getElementById('lightbox');
    if (lightbox) {
        setupLightboxZones();
    }
});

// Back to top button functionality
function setupBackToTop() {
    const btn = document.getElementById('backToTop');
    if (!btn) return;
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    });
    
    // Scroll to top on click
    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}
