from ctypes import c_void_p

from rubicon.objc import CGPoint, NSRange, objc_method, objc_property, send_super
from travertino.size import at_least

from toga_iOS.colors import native_color
from toga_iOS.libs import (
    NSLayoutAttributeBottom,
    NSLayoutAttributeLeading,
    NSLayoutAttributeTop,
    NSLayoutAttributeTrailing,
    NSLayoutConstraint,
    NSLayoutRelationEqual,
    NSTextAlignment,
    UIKeyInput,
    UILabel,
    UITextAutocapitalizationType,
    UITextAutocorrectionType,
    UITextInlinePredictionType,
    UITextSpellCheckingType,
    UITextView,
)
from toga_iOS.widgets.base import Widget


class TogaMultilineTextView(UITextView, protocols=[UIKeyInput]):
    interface = objc_property(object, weak=True)
    impl = objc_property(object, weak=True)

    @objc_method
    def pointInside_withEvent_(self, point: CGPoint, event) -> bool:  # pragma: no cover
        # To keep consistency with non-mobile platforms, we'll resign the
        # responder status when you tap somewhere outside this view. This can't
        # be emulated in CI because it requires an actual touch event; however,
        # it's entirely cosmetic, so we can live with the missing coverage.
        point_inside = send_super(
            __class__,
            self,
            "pointInside:withEvent:",
            point,
            event,
            argtypes=[CGPoint, c_void_p],
        )
        if not bool(point_inside):
            self.resignFirstResponder()
        return point_inside

    @objc_method
    def textViewDidBeginEditing_(self, text_view):
        self.placeholder_label.setHidden(True)

    @objc_method
    def textViewDidEndEditing_(self, text_view):
        self.placeholder_label.setHidden(len(text_view.text) > 0)

    @objc_method
    def textViewDidChange_(self, text_view):
        self.interface.on_change()


class MultilineTextInput(Widget):
    def create(self):
        self.native = TogaMultilineTextView.alloc().init()
        self.native.interface = self.interface
        self.native.impl = self
        self.native.delegate = self.native

        # Placeholder isn't natively supported, so we create our own
        self.placeholder_label = UILabel.alloc().init()
        self.placeholder_label.translatesAutoresizingMaskIntoConstraints = False
        self.placeholder_label.font = self.native.font
        self.placeholder_label.alpha = 0.5
        self.native.addSubview(self.placeholder_label)
        self.constrain_placeholder_label()

        # Delegate needs to update the placeholder depending on
        # input, so we give it just that to avoid a retain cycle
        self.native.placeholder_label = self.placeholder_label

        self.add_constraints()

        self.native.autocorrectionType = UITextAutocorrectionType.Yes
        self.native.spellCheckingType = UITextSpellCheckingType.Yes

    def constrain_placeholder_label(self):
        leading_constraint = NSLayoutConstraint.constraintWithItem(
            self.placeholder_label,
            attribute__1=NSLayoutAttributeLeading,
            relatedBy=NSLayoutRelationEqual,
            toItem=self.native,
            attribute__2=NSLayoutAttributeLeading,
            multiplier=1.0,
            constant=4.0,
        )
        trailing_constraint = NSLayoutConstraint.constraintWithItem(
            self.placeholder_label,
            attribute__1=NSLayoutAttributeTrailing,
            relatedBy=NSLayoutRelationEqual,
            toItem=self.native,
            attribute__2=NSLayoutAttributeTrailing,
            multiplier=1.0,
            constant=0,
        )
        top_constraint = NSLayoutConstraint.constraintWithItem(
            self.placeholder_label,
            attribute__1=NSLayoutAttributeTop,
            relatedBy=NSLayoutRelationEqual,
            toItem=self.native,
            attribute__2=NSLayoutAttributeTop,
            multiplier=1.0,
            constant=8.0,
        )
        bottom_constraint = NSLayoutConstraint.constraintWithItem(
            self.placeholder_label,
            attribute__1=NSLayoutAttributeBottom,
            relatedBy=NSLayoutRelationEqual,
            toItem=self.native,
            attribute__2=NSLayoutAttributeBottom,
            multiplier=1.0,
            constant=0,
        )
        self.native.addConstraints(
            [leading_constraint, trailing_constraint, top_constraint, bottom_constraint]
        )

    def get_placeholder(self):
        return str(self.placeholder_label.text)

    def set_placeholder(self, value):
        self.placeholder_label.text = value

    def get_readonly(self):
        return not self.native.isEditable()

    def set_readonly(self, value):
        self.native.editable = not value

    def get_value(self):
        return str(self.native.text)

    def set_value(self, value):
        self.native.text = value
        self.placeholder_label.setHidden(self.has_focus or len(self.native.text) > 0)
        self.interface.on_change()

    def set_color(self, value):
        color = native_color(value)
        self.native.textColor = color
        self.placeholder_label.textColor = color

    def set_text_align(self, value):
        self.native.textAlignment = NSTextAlignment(value)

    def set_font(self, font):
        native_font = font._impl.native
        self.native.font = native_font
        self.placeholder_label.font = native_font

    def rehint(self):
        self.interface.intrinsic.width = at_least(self.interface._MIN_WIDTH)
        self.interface.intrinsic.height = at_least(self.interface._MIN_HEIGHT)

    def scroll_to_bottom(self):
        self.native.scrollRangeToVisible(NSRange(len(self.native.text) - 1, 1))

    def scroll_to_top(self):
        self.native.scrollRangeToVisible(NSRange(0, 0))

    def set_autocorrect(self, value):
        if isinstance(value, bool):
            if value:
                self.native.autocorrectionType = UITextAutocorrectionType.Yes
            else:
                self.native.autocorrectionType = UITextAutocorrectionType.No
        else:
            raise ValueError("value can only be a boolean")

    def get_autocorrect(self):
        if self.native.autocorrectionType == UITextAutocorrectionType.Yes:
            return True
        else:
            return False

    def set_spellchecker(self, value):
        if isinstance(value, bool):
            if value:
                self.native.spellCheckingType = UITextSpellCheckingType.Yes
            else:
                self.native.spellCheckingType = UITextSpellCheckingType.No
        else:
            raise ValueError("value can only be a boolean")

    def get_spellchecker(self):
        if self.native.spellCheckingType == UITextSpellCheckingType.Yes:
            return True
        else:
            return False

    def set_autocapitalization_type(self, value):
        if isinstance(value, str):
            if value.lower() == "none":
                self.native.autocapitalizationType = UITextAutocapitalizationType.none
            elif value.lower() == "words":
                self.native.autocapitalizationType = UITextAutocapitalizationType.Words
            elif value.lower() == "sentences":
                self.native.autocapitalizationType = (
                    UITextAutocapitalizationType.Sentences
                )
            elif value.lower() == "allcharacters":
                self.native.autocapitalizationType = (
                    UITextAutocapitalizationType.AllCharacters
                )
            else:
                raise ValueError(
                    'value can only be "none", "words", "sentences" or "allcharacters"'
                )
        else:
            raise ValueError(
                'value can only be "none", "words", "sentences" or "allcharacters"'
            )

    def set_inlineprediction_type(self, value):
        if isinstance(value, str):
            if value.lower() == "yes":
                self.native.inlinePredictionType = UITextInlinePredictionType.Yes
            elif value.lower() == "no":
                self.native.inlinePredictionType = UITextInlinePredictionType.No
            elif value.lower() == "default":
                self.native.inlinePredictionType = UITextInlinePredictionType.Default
            else:
                raise ValueError('value can only be "Yes", "No" or "Default"')
        else:
            raise ValueError('value can only be "Yes", "No" or "Default"')
