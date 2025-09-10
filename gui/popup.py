# Copyright 2020 Charles Henry
from aqt.webview import AnkiWebView
from PyQt6 import QtCore, QtGui
from aqt import Qt, QWidget, QGridLayout, QPushButton, QDialog, QHBoxLayout, QMessageBox
from ..anki_utils import AnkiUtils
import logging


class PopupWindow(QWidget):
    """Custom QWidget that handles keyboard shortcuts for Anki popup"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_popup = None  # Will be set later
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        
    def set_parent_popup(self, parent_popup):
        """Set the parent popup reference"""
        self.parent_popup = parent_popup
        
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for answering cards (1, 2, 3, 4) and navigation (space)"""
        if not self.isVisible():
            super().keyPressEvent(event)
            return
            
        key = event.key()
        
        # Handle spacebar for navigation
        if key == Qt.Key.Key_Space or key == 32:  # 32 is ASCII for space
            if hasattr(self.parent_popup, 'bottom_grid'):
                # Check which button is currently visible
                layout_items = self.parent_popup.bottom_grid.count()
                if layout_items > 0:
                    widget = self.parent_popup.bottom_grid.itemAt(0).widget()
                    if widget == self.parent_popup.btn[5]:  # Reveal Question button
                        self.parent_popup.show_question_popup()
                        return
                    elif widget == self.parent_popup.btn[4]:  # Show Answer button
                        self.parent_popup.show_answer_popup()
                        return
        
        # Handle answer shortcuts only when answer buttons are shown
        if hasattr(self.parent_popup, 'cur_button_count') and self.parent_popup.cur_button_count > 0:
            if key == Qt.Key.Key_1 or key == 49:  # 49 is ASCII for '1'
                if self.parent_popup.cur_button_count >= 1:
                    self.parent_popup.send_answer("Again")
                    return
            elif key == Qt.Key.Key_2 or key == 50:  # 50 is ASCII for '2'
                if self.parent_popup.cur_button_count == 2:
                    self.parent_popup.send_answer("Good")
                    return
                elif self.parent_popup.cur_button_count >= 3:
                    self.parent_popup.send_answer("Hard")
                    return
            elif key == Qt.Key.Key_3 or key == 51:  # 51 is ASCII for '3'
                if self.parent_popup.cur_button_count >= 3:
                    self.parent_popup.send_answer("Good")
                    return
            elif key == Qt.Key.Key_4 or key == 52:  # 52 is ASCII for '4'
                if self.parent_popup.cur_button_count >= 4:
                    self.parent_popup.send_answer("Easy")
                    return
        
        # Pass other key events to parent
        super().keyPressEvent(event)


class RuzuPopup(QDialog):

    def __init__(self, parent):
        super().__init__(parent)  # Initialize QDialog
        self.parent = parent
        self.anki_utils = AnkiUtils()
        self.current_card_id = None
        self.cur_button_count = 0
        self.logger = logging.getLogger(__name__.split('.')[0])

        # popup_window (QWidget)
        # -grid (QGridLayout)
        # --card_view (QWebEngineView)
        # --bottom_grid (QGridLayout)
        # ---buttons self.btn[0~3] (QPushButton)

        ###
        # Top level Pop-up Window
        ###
        parent.popup_window = self.popup_window = PopupWindow()
        self.popup_window.set_parent_popup(self)  # Set the reference after creation
        self.popup_window.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.popup_window.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)  # Hide the title bar
        self.popup_window.setWindowTitle("Anki Review")  # Set the title (visible in windows taskbar)
        self.popup_window.setGeometry(0, 0, 400, 300)  # Set window geometry

        ###
        # Card View
        ###
        parent.card_view = self.card_view = AnkiWebView()

        ###
        # Buttons
        ###
        btn_width = 100
        btn_height = 20
        btn_padding = 20
        self.btn = []
        self.btn.append(QPushButton(text="Again"))
        self.btn[0].clicked.connect(lambda _: self.send_answer("Again"))
        self.btn[0].setGeometry(btn_padding, btn_padding, btn_width, btn_height)
        self.btn.append(QPushButton(text="Hard"))
        self.btn[1].clicked.connect(lambda _: self.send_answer("Hard"))
        self.btn[1].setGeometry(btn_padding, btn_padding, btn_width, btn_height)
        self.btn.append(QPushButton(text="Good"))
        self.btn[2].clicked.connect(lambda _: self.send_answer("Good"))
        self.btn[2].setGeometry(btn_padding, btn_padding, btn_width, btn_height)
        self.btn.append(QPushButton(text="Easy"))
        self.btn[3].clicked.connect(lambda _: self.send_answer("Easy"))
        self.btn[3].setGeometry(btn_padding, btn_padding, btn_width, btn_height)
        self.btn.append(QPushButton(text="Show Answer"))
        self.btn[4].setGeometry(btn_padding, btn_padding, btn_width, btn_height)
        self.btn[4].clicked.connect(lambda _: self.show_answer_popup())
        self.btn.append(QPushButton(text="Reveal Question"))
        self.btn[5].setGeometry(btn_padding, btn_padding, btn_width, btn_height)
        self.btn[5].clicked.connect(lambda _: self.show_question_popup())

        ###
        # Layout management - Add objects to main pop-up window
        ###
        parent.grid = self.grid = QGridLayout()
        parent.bottom_grid = self.bottom_grid = QHBoxLayout()
        # self.bottom_grid.setVerticalSpacing(10)
        self.bottom_grid.setContentsMargins(10, 5, 10, 10)
        for i in range(4):
            self.bottom_grid.addWidget(self.btn[i])
        parent.bottom_grid_2 = self.bottom_grid_2 = QHBoxLayout()  # Used to hide buttons when needed
        parent.bottom_wid_2 = self.bottom_wid_2 = QWidget()  # Used to hide buttons when needed
        self.bottom_wid_2.setLayout(self.bottom_grid_2)  # Used to hide buttons when needed
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.addWidget(self.card_view)
        self.grid.addLayout(self.bottom_grid, 1, 0)
        self.popup_window.setLayout(self.grid)

    def set_card_position(self):
        # Move to bottom right of screen
        # https://stackoverflow.com/questions/28322073/move-qmessagebox-to-bottom-right-corner-of-the-screen
        # https://forum.qt.io/topic/134570/qapplication-desktop-screengeometry-not-work-in-qt6
        screen_geometry = self.parent.app.primaryScreen().availableGeometry()
        screen_geo = screen_geometry.bottomRight()
        msg_geo = self.popup_window.frameGeometry()
        msg_geo.moveBottomRight(screen_geo)
        self.popup_window.move(msg_geo.topLeft())

    def show_show_button(self):
        for i in range(6):
            self.bottom_grid_2.addWidget(self.btn[i])  # Remove all buttons
        self.bottom_grid.addWidget(self.btn[5])

    def show_question_button(self):
        for i in range(6):
            self.bottom_grid_2.addWidget(self.btn[i])  # Remove all buttons
        self.bottom_grid.addWidget(self.btn[4])

    def show_answer_buttons(self):
        # TODO - Take in actual buttons tuple?
        for i in range(6):
            self.bottom_grid_2.addWidget(self.btn[i])  # Remove all buttons
        if self.cur_button_count == 2:
            self.bottom_grid.addWidget(self.btn[0])  # Again
            self.bottom_grid.addWidget(self.btn[2])  # Good
        elif self.cur_button_count == 3:
            self.bottom_grid.addWidget(self.btn[0])  # Again
            self.bottom_grid.addWidget(self.btn[2])  # Good
            self.bottom_grid.addWidget(self.btn[3])  # Easy
        else:
            for i in range(4):
                self.bottom_grid.addWidget(self.btn[i])  # Again, Hard, Good, Easy

    def reset_card(self):
        self.card_view.setHtml(None)

    def prep_card(self):
        # Update card with 'Reveal card' html
        self.card_view.setHtml("""
                    <!doctype html>
                    <html>
                        <head></head>
                        <body>
                            <div style="margin: auto; text-align: center; line-height: 90vh; font-size: 60px;">🔔</div>
                        </body>
                    </html>
                """)

    def update_card(self, card):
        # TODO - Look into using existing AnkiWebView object to render duplicate card with full compatibility
        self.card_view.setHtml("""
                    <!doctype html>
                    <html class=" webkit chrome win js">
                        <head>
                            <title>main webview</title>
                            %(base)s
                            <style>
                                body { zoom: 1; background: #f0f0f0; direction: ltr; font-size:12px;font-family:"Segoe UI"; }
                                button { font-family:"Segoe UI"; }
                                :focus { outline: 1px solid #0078d7; }
                            </style>
                        </head>

                        <body class="card card2 isWin">
                            <div id="qa" style="opacity: 1;">
                                """ + card + """
                            </div>
                        </body>
                    </html>
                """ % dict(base=self.anki_utils.main_window().baseHTML()))

    def pre_popup_validate(self):
        self.logger.info('pre_popup_validate...')
        # Get current deck from config
        current_deck = self.anki_utils.get_config()['deck']

        # Check that review is active and current deck is as expected (if not then start review)
        if not self.anki_utils.review_is_active() or current_deck != self.anki_utils.selected_deck():
            self.logger.info('Start review...')
            review_started = self.anki_utils.move_to_review_state(current_deck)
            self.logger.info('review_started: %s' % review_started)
            if not review_started:
                raise Exception('Failed to start review...')
            if review_started and not self.anki_utils.review_is_active():
                self.logger.info('No cards left to review')
                raise Exception('No cards available for review')

    def show_answer_popup(self):
        self.logger.info('show_answer_popup...')
        self.popup_window.hide()
        try:
            self.pre_popup_validate()
        except Exception as e:
            self.logger.info('Cannot show answer popup: %s' % str(e))
            QMessageBox.information(self.popup_window, "No Review Available", "There are no cards available for review at this time.")
            return
        if not self.anki_utils.review_is_active():
            QMessageBox.information(self.popup_window, "No Review Active", "There are no cards available for review at this time.")
            return

        # TODO - Extra if this fails for some reason
        show_ans_result = self.anki_utils.show_answer()
        self.logger.debug('Show Answer Result: %s' % show_ans_result)

        # Collect card details (html, css, buttons)
        current_card = self.anki_utils.get_current_card()
        if self.current_card_id != current_card['card_id']:
            self.logger.info('Card has changed, show new card...')
            self.show_question_popup()
        else:
            self.cur_button_count = len(current_card['button_list'])
            self.show_answer_buttons()
            self.update_card(current_card['answer'])

            # Show pop-up
            self.set_card_position()
            self.popup_window.show()
            self.popup_window.setFocus()  # Set focus for keyboard input
            self.popup_window.setFocus()  # Set focus for keyboard input

    def show_popup(self):
        self.logger.info('show_popup... called')
        
        # Validate that we can show a popup (check for available cards)
        current_deck = self.anki_utils.get_config()['deck']
        self.logger.info('Current deck: %s, Selected deck: %s' % (current_deck, self.anki_utils.selected_deck()))
        self.logger.info('Review active: %s' % self.anki_utils.review_is_active())
        
        if not self.anki_utils.review_is_active() or current_deck != self.anki_utils.selected_deck():
            self.logger.info('Start review for popup validation...')
            review_started = self.anki_utils.move_to_review_state(current_deck)
            self.logger.info('review_started: %s' % review_started)
            if not review_started or not self.anki_utils.review_is_active():
                self.logger.info('No cards available for review, not showing popup')
                return
        
        self.logger.info('Showing popup...')
        # Enter pre reveal state based on user config
        if self.anki_utils.get_config()['click_to_reveal']:
            self.hide_card()
            self.prep_card()
            self.show_show_button()
            self.set_card_position()
            self.popup_window.show()
            self.popup_window.setFocus()  # Set focus for keyboard input
            self.logger.info('Popup shown with click_to_reveal')
        else:
            self.logger.info('Calling show_question_popup...')
            self.show_question_popup()

    def show_question_popup(self):
        self.logger.info('show_question_popup... called')
        self.popup_window.hide()
        try:
            self.pre_popup_validate()
            self.logger.info('pre_popup_validate passed')
        except Exception as e:
            self.logger.info('Cannot show question popup: %s' % str(e))
            QMessageBox.information(self.popup_window, "No Review Available", "There are no cards available for review at this time.")
            return
        if not self.anki_utils.review_is_active():
            self.logger.info('Review not active after validation')
            QMessageBox.information(self.popup_window, "No Review Active", "There are no cards available for review at this time.")
            return
        
        self.logger.info('Showing question popup...')
        show_q_result = self.anki_utils.show_question()
        self.logger.debug('Show Question Result: %s' % show_q_result)

        # Collect card details (html, css, buttons)
        current_card = self.anki_utils.get_current_card()
        self.current_card_id = current_card['card_id']
        self.logger.debug('Setting current card to %s' % current_card['card_id'])
        self.update_card(current_card['question'])
        self.show_question_button()

        # Show pop-up
        self.set_card_position()
        self.popup_window.show()
        self.popup_window.setFocus()  # Set focus for keyboard input
        self.logger.info('Question popup shown')

    def send_answer(self, ease_name):
        # TODO - Clean this up, not elegant at all
        if self.cur_button_count == 2:
            if ease_name == "Again":
                ease = 1
            elif ease_name == "Good":
                ease = 2
            else:
                raise Exception('Invalid ease used, expected [Again] or [Good] but got [%s]' % ease_name)
        elif self.cur_button_count == 3:
            if ease_name == "Again":
                ease = 1
            elif ease_name == "Good":
                ease = 2
            elif ease_name == "Easy":
                ease = 3
            else:
                raise Exception('Invalid ease used, expected [Again], [Good] or [Easy] but got [%s]' % ease_name)
        else:
            if ease_name == "Again":
                ease = 1
            elif ease_name == "Hard":
                ease = 2
            elif ease_name == "Good":
                ease = 3
            elif ease_name == "Easy":
                ease = 4
            else:
                raise Exception('Invalid ease used, expected '
                                '[Again], [Hard], [Good] or [Easy] but got [%s]' % ease_name)

        self.logger.debug('send_answer with ease_name [%s]' % ease_name)
        self.logger.debug('send_answer with ease [%s]' % ease)

        # Get current card and check it's the expected card
        current_card = self.anki_utils.get_current_card()
        if current_card['card_id'] == self.current_card_id:
            # Send the answer
            answer_result = self.anki_utils.answer_card(ease)
            self.logger.debug('answer_result: %s' % answer_result)
        else:
            # TODO - Handle this better, notify user?
            self.logger.warning('The card you tried to answer is no longer the card being reviewed...')

        self.hide_card()

    def hide_card(self):
        self.reset_card()
        self.popup_window.hide()
        # Don't move to overview state immediately after answering to avoid interfering with Anki's review flow
        # current_deck = self.anki_utils.get_config()['deck']
        # review_ended = self.anki_utils.move_to_overview_state(current_deck)
        # self.logger.info('review_ended: %s' % review_ended)
