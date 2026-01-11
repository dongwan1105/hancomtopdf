/**
 * 한글 → PDF 변환기 클라이언트
 * 파일 업로드, 변환 요청, 결과 다운로드를 처리합니다.
 */

// =====================================================
// 상태 관리
// =====================================================

const state = {
    files: [],      // 업로드된 파일 목록
    taskId: null,   // 현재 변환 작업 ID
    polling: null   // 상태 폴링 인터벌
};

// =====================================================
// DOM 요소
// =====================================================

const elements = {
    dropzone: document.getElementById('dropzone'),
    fileInput: document.getElementById('file-input'),
    fileListContainer: document.getElementById('file-list-container'),
    fileList: document.getElementById('file-list'),
    clearBtn: document.getElementById('clear-btn'),
    convertBtn: document.getElementById('convert-btn'),
    progressContainer: document.getElementById('progress-container'),
    progressText: document.getElementById('progress-text'),
    progressCount: document.getElementById('progress-count'),
    progressFill: document.getElementById('progress-fill'),
    resultsContainer: document.getElementById('results-container'),
    resultsList: document.getElementById('results-list'),
    downloadAllBtn: document.getElementById('download-all-btn'),
    toastContainer: document.getElementById('toast-container')
};

// =====================================================
// 유틸리티 함수
// =====================================================

/**
 * 파일 크기를 읽기 쉬운 형식으로 변환
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 토스트 알림 표시
 */
function showToast(message, type = 'info') {
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <div class="toast-content">
            <span class="toast-message">${message}</span>
        </div>
    `;

    elements.toastContainer.appendChild(toast);

    // 3초 후 제거
    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * 파일 확장자 확인
 */
function isValidFile(file) {
    const validExtensions = ['.hwp', '.hwpx'];
    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    return validExtensions.includes(extension);
}

// =====================================================
// 파일 관리
// =====================================================

/**
 * 파일 목록에 파일 추가
 */
function addFiles(newFiles) {
    let addedCount = 0;

    for (const file of newFiles) {
        if (!isValidFile(file)) {
            showToast(`"${file.name}"은 지원하지 않는 형식입니다`, 'warning');
            continue;
        }

        // 중복 확인
        if (state.files.some(f => f.name === file.name && f.size === file.size)) {
            showToast(`"${file.name}"은 이미 추가되었습니다`, 'warning');
            continue;
        }

        state.files.push(file);
        addedCount++;
    }

    if (addedCount > 0) {
        showToast(`${addedCount}개 파일이 추가되었습니다`, 'success');
        renderFileList();
    }
}

/**
 * 파일 목록에서 파일 제거
 */
function removeFile(index) {
    const removedFile = state.files.splice(index, 1)[0];
    showToast(`"${removedFile.name}"이 제거되었습니다`, 'info');
    renderFileList();
}

/**
 * 파일 목록 전체 비우기
 */
function clearFiles() {
    state.files = [];
    renderFileList();
    showToast('목록이 비워졌습니다', 'info');
}

/**
 * 파일 목록 렌더링
 */
function renderFileList() {
    if (state.files.length === 0) {
        elements.fileListContainer.classList.remove('show');
        return;
    }

    elements.fileListContainer.classList.add('show');
    elements.fileList.innerHTML = state.files.map((file, index) => `
        <li class="file-item">
            <div class="file-icon">📄</div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
            <button class="file-remove" onclick="removeFile(${index})" title="제거">
                ✕
            </button>
        </li>
    `).join('');
}

// =====================================================
// 변환 처리
// =====================================================

/**
 * 변환 시작
 */
async function startConversion() {
    if (state.files.length === 0) {
        showToast('변환할 파일을 추가해주세요', 'warning');
        return;
    }

    // UI 업데이트
    elements.convertBtn.disabled = true;
    elements.clearBtn.disabled = true;
    elements.progressContainer.classList.add('show');
    elements.resultsContainer.classList.remove('show');
    updateProgress(0, state.files.length, '변환 준비 중...');

    // FormData 생성
    const formData = new FormData();
    for (const file of state.files) {
        formData.append('files', file);
    }

    try {
        // 변환 요청
        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '변환 요청 실패');
        }

        const data = await response.json();
        state.taskId = data.task_id;

        showToast('변환이 시작되었습니다', 'info');

        // 상태 폴링 시작
        startPolling();

    } catch (error) {
        showToast(error.message, 'error');
        resetUI();
    }
}

/**
 * 상태 폴링
 */
function startPolling() {
    // 기존 폴링 중지
    if (state.polling) {
        clearInterval(state.polling);
    }

    state.polling = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${state.taskId}`);

            if (!response.ok) {
                throw new Error('상태 확인 실패');
            }

            const data = await response.json();

            // 진행 상태 업데이트
            updateProgress(data.completed, data.total, '변환 중...');

            // 완료 확인
            if (data.status === 'completed') {
                stopPolling();
                showResults(data.results);
            }

        } catch (error) {
            stopPolling();
            showToast('상태 확인 중 오류가 발생했습니다', 'error');
            resetUI();
        }
    }, 500); // 0.5초마다 폴링
}

/**
 * 폴링 중지
 */
function stopPolling() {
    if (state.polling) {
        clearInterval(state.polling);
        state.polling = null;
    }
}

/**
 * 진행 상태 업데이트
 */
function updateProgress(completed, total, text) {
    const percent = total > 0 ? (completed / total) * 100 : 0;
    elements.progressFill.style.width = `${percent}%`;
    elements.progressCount.textContent = `${completed} / ${total}`;
    elements.progressText.textContent = text;
}

/**
 * 결과 표시
 */
function showResults(results) {
    elements.progressContainer.classList.remove('show');
    elements.resultsContainer.classList.add('show');

    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;

    if (successCount > 0 && failCount === 0) {
        showToast(`${successCount}개 파일 변환 완료!`, 'success');
    } else if (successCount > 0) {
        showToast(`${successCount}개 성공, ${failCount}개 실패`, 'warning');
    } else {
        showToast('모든 파일 변환 실패', 'error');
    }

    elements.resultsList.innerHTML = results.map(result => {
        if (result.success) {
            return `
                <li class="result-item">
                    <div class="result-icon success">✓</div>
                    <div class="result-info">
                        <div class="result-name">${result.filename}</div>
                        <div class="result-status success">변환 완료</div>
                    </div>
                    <a href="/api/download/${state.taskId}/${encodeURIComponent(result.pdf_filename)}" 
                       class="result-download" download>
                        📥 다운로드
                    </a>
                </li>
            `;
        } else {
            return `
                <li class="result-item">
                    <div class="result-icon error">✕</div>
                    <div class="result-info">
                        <div class="result-name">${result.filename}</div>
                        <div class="result-status error">${result.error || '변환 실패'}</div>
                    </div>
                </li>
            `;
        }
    }).join('');

    // 성공한 파일이 있으면 전체 다운로드 버튼 활성화
    elements.downloadAllBtn.disabled = successCount === 0;
    elements.downloadAllBtn.style.display = successCount > 1 ? 'inline-flex' : 'none';

    resetUI();
}

/**
 * UI 리셋
 */
function resetUI() {
    elements.convertBtn.disabled = false;
    elements.clearBtn.disabled = false;
}

/**
 * 전체 다운로드
 */
function downloadAll() {
    if (state.taskId) {
        window.location.href = `/api/download-all/${state.taskId}`;
    }
}

// =====================================================
// 드래그 앤 드롭
// =====================================================

function setupDragAndDrop() {
    const dropzone = elements.dropzone;

    // 기본 이벤트 방지
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // 드래그 진입/오버
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.add('dragover');
        });
    });

    // 드래그 이탈
    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.remove('dragover');
        });
    });

    // 파일 드롭
    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            addFiles(files);
        }
    });

    // 클릭으로 파일 선택
    dropzone.addEventListener('click', () => {
        elements.fileInput.click();
    });

    // 파일 입력 변경
    elements.fileInput.addEventListener('change', (e) => {
        const files = e.target.files;
        if (files.length > 0) {
            addFiles(files);
        }
        // 동일 파일 재선택을 위해 값 초기화
        e.target.value = '';
    });
}

// =====================================================
// 이벤트 리스너
// =====================================================

function setupEventListeners() {
    // 목록 비우기
    elements.clearBtn.addEventListener('click', clearFiles);

    // 변환 시작
    elements.convertBtn.addEventListener('click', startConversion);

    // 전체 다운로드
    elements.downloadAllBtn.addEventListener('click', downloadAll);
}

// =====================================================
// 초기화
// =====================================================

document.addEventListener('DOMContentLoaded', () => {
    setupDragAndDrop();
    setupEventListeners();

    console.log('한글 → PDF 변환기가 준비되었습니다.');
});
