"""
한컴오피스 한글 문서를 PDF로 변환하는 모듈
pyhwpx 또는 COM Automation을 사용하여 한컴오피스를 제어합니다.
"""

import os
import time

# pyhwpx 사용 시도, 없으면 직접 COM 사용
try:
    from pyhwpx import Hwp
    USE_PYHWPX = True
except ImportError:
    USE_PYHWPX = False
    import pythoncom
    import win32com.client as win32


class HwpToPdfConverter:
    """한글 문서를 PDF로 변환하는 클래스"""
    
    def __init__(self):
        self.hwp = None
    
    def convert(self, hwp_path: str, pdf_path: str = None) -> str:
        """
        한글 문서를 PDF로 변환
        
        Args:
            hwp_path: 변환할 한글 문서 경로 (.hwp 또는 .hwpx)
            pdf_path: 저장할 PDF 경로 (None이면 원본과 같은 위치에 같은 이름으로 저장)
        
        Returns:
            생성된 PDF 파일 경로
        """
        # 경로 정규화
        hwp_path = os.path.abspath(hwp_path)
        
        if not os.path.exists(hwp_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {hwp_path}")
        
        # PDF 경로 결정
        if pdf_path is None:
            base_name = os.path.splitext(hwp_path)[0]
            pdf_path = base_name + ".pdf"
        else:
            pdf_path = os.path.abspath(pdf_path)
        
        # 출력 디렉토리 확인
        output_dir = os.path.dirname(pdf_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        if USE_PYHWPX:
            return self._convert_with_pyhwpx(hwp_path, pdf_path)
        else:
            return self._convert_with_com(hwp_path, pdf_path)
    
    def _convert_with_pyhwpx(self, hwp_path: str, pdf_path: str) -> str:
        """pyhwpx를 사용한 변환"""
        hwp = None
        try:
            # pyhwpx로 한글 열기
            hwp = Hwp(visible=False)
            hwp.open(hwp_path)
            
            # PDF로 저장 - save_as 메서드 사용
            hwp.save_as(pdf_path, format="PDF")
            
            # 문서 닫기
            hwp.clear()
            hwp.quit()
            hwp = None
            
            # PDF 파일 생성 확인
            if not os.path.exists(pdf_path):
                raise RuntimeError("PDF 파일이 생성되지 않았습니다")
            
            return pdf_path
            
        except Exception as e:
            if hwp:
                try:
                    hwp.quit()
                except:
                    pass
            raise RuntimeError(f"변환 실패 (pyhwpx): {str(e)}")
    
    def _convert_with_com(self, hwp_path: str, pdf_path: str) -> str:
        """직접 COM을 사용한 변환"""
        hwp = None
        try:
            import pythoncom
            pythoncom.CoInitialize()
            
            # 한컴오피스 COM 객체 생성
            hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
            
            # 보안 모듈 등록 (자동화 허용)
            hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
            
            # 백그라운드에서 실행 (UI 숨김)
            hwp.XHwpWindows.Item(0).Visible = False
            
            # 한글 문서 열기
            hwp.Open(hwp_path, "HWP", "forceopen:true")
            
            # PDF로 저장 - 방법 1: HAction 사용
            act = hwp.CreateAction("FileSaveAs_S")
            pset = act.CreateSet()
            act.GetDefault(pset)
            pset.SetItem("Format", "PDF")
            pset.SetItem("filename", pdf_path)
            act.Execute(pset)
            
            # 문서 닫기
            hwp.Clear(1)
            
            # PDF 파일 생성 확인
            time.sleep(0.5)  # 파일 저장 대기
            if not os.path.exists(pdf_path):
                raise RuntimeError("PDF 파일이 생성되지 않았습니다")
            
            return pdf_path
            
        except Exception as e:
            raise RuntimeError(f"변환 실패 (COM): {str(e)}")
        finally:
            if hwp:
                try:
                    hwp.Quit()
                except:
                    pass
            try:
                pythoncom.CoUninitialize()
            except:
                pass
    
    def convert_multiple(self, hwp_paths: list, output_dir: str = None) -> list:
        """
        여러 한글 문서를 PDF로 일괄 변환
        
        Args:
            hwp_paths: 변환할 한글 문서 경로 리스트
            output_dir: PDF를 저장할 디렉토리 (None이면 각 원본 위치에 저장)
        
        Returns:
            변환 결과 리스트 [{"hwp": str, "pdf": str, "success": bool, "error": str}, ...]
        """
        results = []
        
        for hwp_path in hwp_paths:
            result = {
                "hwp": hwp_path,
                "pdf": None,
                "success": False,
                "error": None
            }
            
            try:
                if output_dir:
                    base_name = os.path.splitext(os.path.basename(hwp_path))[0]
                    pdf_path = os.path.join(output_dir, base_name + ".pdf")
                else:
                    pdf_path = None
                
                result["pdf"] = self.convert(hwp_path, pdf_path)
                result["success"] = True
                
            except Exception as e:
                result["error"] = str(e)
            
            results.append(result)
        
        return results


def convert_hwp_to_pdf(hwp_path: str, pdf_path: str = None) -> str:
    """
    편의 함수: 단일 한글 문서를 PDF로 변환
    
    Args:
        hwp_path: 변환할 한글 문서 경로
        pdf_path: 저장할 PDF 경로 (선택)
    
    Returns:
        생성된 PDF 파일 경로
    """
    converter = HwpToPdfConverter()
    return converter.convert(hwp_path, pdf_path)


if __name__ == "__main__":
    # 테스트
    import sys
    
    print(f"pyhwpx 사용: {USE_PYHWPX}")
    
    if len(sys.argv) < 2:
        print("사용법: python converter.py <hwp_file>")
        sys.exit(1)
    
    hwp_file = sys.argv[1]
    print(f"변환 중: {hwp_file}")
    
    try:
        pdf_file = convert_hwp_to_pdf(hwp_file)
        print(f"변환 완료: {pdf_file}")
    except Exception as e:
        print(f"오류: {e}")
        sys.exit(1)
