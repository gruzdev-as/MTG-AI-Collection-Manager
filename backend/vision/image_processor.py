import cv2
import numpy as np


class ImageProcesser:
    """Using for processing images in a thread."""

    def find_big_contours(
        self,
        frame: np.ndarray,
        epsilon_factor: float = 0.05,
        min_area: int = 50_000,
    ) -> tuple[np.ndarray, list[cv2.typing.MatLike]]:
        """Detect contours on an image using OpenCV and keeps only those that are rectangular-like.

        Args:
            frame (np.array): The frame captured from the camera on which contours are detected.
            epsilon_factor (float, optional): Factor for approximating arcs in contours.
                A lower value results in a more accurate approximation. Defaults to 0.05.
            min_area (int, optional): Minimum area for contours to be kept. This is
                empirically determined to filter out smaller, irrelevant contours. Defaults to 50,000.

        Returns:
            Tuple[np.ndarray, list[cv2.typing.MatLike]]: A tuple where:
                - The first element is the image with detected contours drawn on it.
                - The second element is a list of contours that match the specified criteria.

        """
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (15, 15), 0)

        if np.mean(gray) < 127:
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_to_keep = []

        for contour in contours:
            epsilon = epsilon_factor * cv2.arcLength(contour, closed=True)
            approx = cv2.approxPolyDP(contour, epsilon, closed=True)
            area = cv2.contourArea(contour)
            if len(approx) != 4 or area < min_area or not cv2.isContourConvex(approx):
                continue
            contours_to_keep.append(contour)

        contour_image = frame.copy()
        # TODO @gruzdev-as: Should draw contours_to_keep instead of all contours for the final result
        cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 15)

        return contour_image, contours_to_keep

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order points in the correct order (tl, tr, br, bl)."""
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def crop_warp_image_from_contour(
        self,
        image: np.ndarray,
        contour: cv2.typing.MatLike,
        target_size: tuple[int, int] | None = None,
    ) -> np.ndarray:
        """Crops a specified contour from an image and applies perspective correction.

        Args:
            image (np.ndarray): Original image from which to crop.
            contour (cv2.typing.MatLike): Contour representing the crop area.
            target_size (tuple[int, int] | None, optional): Desired size for the output image. Defaults to None.

        Returns:
            np.ndarray: Cropped and warped image.

        """
        epsilon = 0.05 * cv2.arcLength(contour, closed=True)
        approx = cv2.approxPolyDP(contour, epsilon, closed=True)
        approx = self._order_points(approx.reshape(4, 2)).astype("float32")
        (tl, tr, br, bl) = approx

        width_top = np.linalg.norm(tr - tl)
        width_bottom = np.linalg.norm(br - bl)
        width = max(int(width_top), int(width_bottom))

        height_right = np.linalg.norm(br - tr)
        height_left = np.linalg.norm(bl - tl)
        height = max(int(height_right), int(height_left))

        destination = np.array(
            [
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1],
            ],
            dtype="float32",
        )

        M = cv2.getPerspectiveTransform(approx, destination)
        warped_image = cv2.warpPerspective(image, M, (width, height))

        if target_size:
            return cv2.resize(warped_image, target_size)

        return warped_image
