# Copyright (C) 2007, Eduardo Silva (edsiper@gmail.com)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import gtk
import gobject
import time
import hippo

from sugar.graphics import animator
from sugar import _sugarext

ALIGNMENT_AUTOMATIC     = 0
ALIGNMENT_BOTTOM_LEFT   = 1
ALIGNMENT_BOTTOM_RIGHT  = 2
ALIGNMENT_LEFT_BOTTOM   = 3
ALIGNMENT_LEFT_TOP      = 4
ALIGNMENT_RIGHT_BOTTOM  = 5
ALIGNMENT_RIGHT_TOP     = 6
ALIGNMENT_TOP_LEFT      = 7
ALIGNMENT_TOP_RIGHT     = 8

class Palette(gobject.GObject):
    __gtype_name__ = 'SugarPalette'

    __gproperties__ = {
        'invoker'    : (object, None, None,
                        gobject.PARAM_READWRITE),
        'alignment'  : (gobject.TYPE_INT, None, None, 0, 8,
                        ALIGNMENT_AUTOMATIC,
                        gobject.PARAM_READWRITE)
    }

    def __init__(self, label, accel_path=None):
        gobject.GObject.__init__(self)

        self._alignment = ALIGNMENT_AUTOMATIC

        self._popup_anim = animator.Animator(0.3, 10)
        self._popup_anim.add(_PopupAnimation(self))

        self._popdown_anim = animator.Animator(0.6, 10)
        self._popdown_anim.add(_PopdownAnimation(self))

        self._menu = _sugarext.Menu()

        primary = _PrimaryMenuItem(label, accel_path)
        self._menu.append(primary)
        primary.show()

        self._separator = gtk.SeparatorMenuItem()
        self._menu.append(self._separator)

        self._content = _ContentMenuItem()
        self._menu.append(self._content)

        self._button_bar = _ButtonBarMenuItem()
        self._menu.append(self._button_bar)

        self._menu.connect('enter-notify-event',
                           self._enter_notify_event_cb)
        self._menu.connect('leave-notify-event',
                           self._leave_notify_event_cb)
        self._menu.connect('button-press-event',
                           self._button_press_event_cb)

    def append_menu_item(self, item):
        self._separator.show()
        self._menu.insert(item, len(self._menu.get_children()) - 2)

    def insert_menu_item(self, item, index=-1):
        self._separator.show()
        if index < 0:
            self._menu.insert(item, len(self._menu.get_children()) - 2)
        else:
            self._menu.insert(item, index + 2)

    def remove_menu_item(self, index):
        if index > len(self._menu.get_children()) - 4:
            raise ValueError('index %i out of range' % index)
        self._menu.remove(self._menu.get_children()[index + 2])
        if len(self._menu.get_children()) == 0:
            self._separator.hide()

    def menu_item_count(self):
        return len(self._menu.get_children()) - 4
        
    def set_content(self, widget):
        self._content.set_widget(widget)
        self._content.show()

    def append_button(self, button):
        self._button_bar.append_button(button)
        self._button_bar.show()
        
    def do_set_property(self, pspec, value):
        if pspec.name == 'invoker':
            self._invoker = value
            self._invoker.add_listener(self)
        elif pspec.name == 'alignment':
            self._alignment = value
        else:
            raise AssertionError

    def _get_position(self):
        if self._alignment == ALIGNMENT_AUTOMATIC:
            x, y = self._try_position(ALIGNMENT_BOTTOM_LEFT)
            if x == -1:
                x, y = self._try_position(ALIGNMENT_BOTTOM_RIGHT)
            if x == -1:
                x, y = self._try_position(ALIGNMENT_LEFT_BOTTOM)
            if x == -1:
                x, y = self._try_position(ALIGNMENT_LEFT_TOP)
            if x == -1:
                x, y = self._try_position(ALIGNMENT_RIGHT_BOTTOM)
            if x == -1:
                x, y = self._try_position(ALIGNMENT_RIGHT_TOP)
            if x == -1:
                x, y = self._try_position(ALIGNMENT_LEFT_BOTTOM)
            if x == -1:
                x, y = self._try_position(ALIGNMENT_LEFT_BOTTOM)
        else:
            x, y = self._position_for_alignment(self._alignment)

        return (x, y)

    def _try_position(self, alignment):
        x, y = self._position_for_alignment(alignment)
        allocation = self._menu.get_allocation()

        if (x + allocation.width > gtk.gdk.screen_width()) or \
           (y + allocation.height > gtk.gdk.screen_height()):
            return (-1, -1)
        else:
            return (x, y)

    def _position_for_alignment(self, alignment):
        # Invoker: x, y, width and height
        inv_rect = self._invoker.get_rect()
        palette_rect = self._menu.get_allocation()

        if alignment == ALIGNMENT_BOTTOM_LEFT:
            move_x = inv_rect.x
            move_y = inv_rect.y + inv_rect.height
        elif alignment == ALIGNMENT_BOTTOM_RIGHT:
            move_x = (inv_rect.x + inv_rect.width) - palette_rect.width
            move_y = inv_rect.y + inv_rect.height
        elif alignment == ALIGNMENT_LEFT_BOTTOM:
            move_x = inv_rect.x - palette_rect.width
            move_y = inv_rect.y
        elif alignment == ALIGNMENT_LEFT_TOP:
            move_x = inv_rect.x - palette_rect.width
            move_y = (inv_rect.y + inv_rect.height) - palette_rect.height
        elif alignment == ALIGNMENT_RIGHT_BOTTOM:
            move_x = inv_rect.x + inv_rect.width
            move_y = inv_rect.y
        elif alignment == ALIGNMENT_RIGHT_TOP:
            move_x = inv_rect.x + inv_rect.width
            move_y = (inv_rect.y + inv_rect.height) - palette_rect.height
        elif alignment == ALIGNMENT_TOP_LEFT:
            move_x = inv_rect.x
            move_y = inv_rect.y - palette_rect.height
        elif alignment == ALIGNMENT_TOP_RIGHT:
            move_x = (inv_rect.x + inv_rect.width) - palette_rect.width
            move_y = inv_rect.y - palette_rect.height

        return move_x, move_y

    def _show(self):
        x, y = self._get_position()
        self._menu.popup(x, y)

    def _hide(self):
        self._menu.popdown()

    def popup(self):
        self._popdown_anim.stop()
        self._popup_anim.start()

    def popdown(self):
        self._popup_anim.stop()
        self._popdown_anim.start()

    def invoker_mouse_enter(self):
        print 'Invoker enter'
        self.popup()

    def invoker_mouse_leave(self):
        self.popdown()

    def _enter_notify_event_cb(self, widget, event):
        print 'Enter notify'
        if event.detail == gtk.gdk.NOTIFY_NONLINEAR:
            self._popdown_anim.stop()

    def _leave_notify_event_cb(self, widget, event):
        if event.detail == gtk.gdk.NOTIFY_NONLINEAR:
            self.popdown()

    def _button_press_event_cb(self, widget, event):
        pass

class _PrimaryMenuItem(gtk.MenuItem):
    def __init__(self, label, accel_path):
        gtk.MenuItem.__init__(self)

        label = gtk.AccelLabel(label)
        label.set_accel_widget(self)

        if accel_path:
            self.set_accel_path(accel_path)
            label.set_alignment(0.0, 0.5)

        self.add(label)
        label.show()

class _ContentMenuItem(gtk.MenuItem):
    def __init__(self):
        gtk.MenuItem.__init__(self)

    def set_widget(self, widget):
        if self.child:
            self.remove(self.child)
        self.add(widget)

class _ButtonBarMenuItem(gtk.MenuItem):
    def __init__(self):
        gtk.MenuItem.__init__(self)

        self._hbar = gtk.HButtonBox()
        self.add(self._hbar)
        self._hbar.show()

    def append_button(self, button):
        self._hbar.pack_start(button)

class _PopupAnimation(animator.Animation):
    def __init__(self, palette):
        animator.Animation.__init__(self, 0.0, 1.0)
        self._palette = palette

    def next_frame(self, current):
        if current == 1.0:
            self._palette._show()

class _PopdownAnimation(animator.Animation):
    def __init__(self, palette):
        animator.Animation.__init__(self, 0.0, 1.0)
        self._palette = palette

    def next_frame(self, current):
        if current == 1.0:
            self._palette._hide()

class Invoker(object):
    def __init__(self):
        self._listeners = []

    def add_listener(self, listener):
        self._listeners.append(listener)

    def notify_mouse_enter(self):
        for listener in self._listeners:
            listener.invoker_mouse_enter()

    def notify_mouse_leave(self):
        for listener in self._listeners:
            listener.invoker_mouse_leave()

class WidgetInvoker(Invoker):
    def __init__(self, widget):
        Invoker.__init__(self)
        self._widget = widget

        widget.connect('enter-notify-event', self._enter_notify_event_cb)
        widget.connect('leave-notify-event', self._leave_notify_event_cb)

    def get_rect(self):
        win_x, win_y = self._widget.window.get_origin()
        rectangle = self._widget.get_allocation()

        x = win_x + rectangle.x
        y = win_y + rectangle.y
        width = rectangle.width
        height = rectangle.height

        return gtk.gdk.Rectangle(x, y, width, height)

    def _enter_notify_event_cb(self, widget, event):
        self.notify_mouse_enter()

    def _leave_notify_event_cb(self, widget, event):
        self.notify_mouse_leave()

class CanvasInvoker(Invoker):
    def __init__(self, item):
        Invoker.__init__(self)
        self._item = item

        item.connect('motion-notify-event',
                     self._motion_notify_event_cb)

    def get_rect(self):
        context = self._item.get_context()
        if context:
            x, y = context.translate_to_screen(self._item)

        width, height = self._item.get_allocation()

        return gtk.gdk.Rectangle(x, y, width, height)

    def _motion_notify_event_cb(self, button, event):
        if event.detail == hippo.MOTION_DETAIL_ENTER:
            self.notify_mouse_enter()
        elif event.detail == hippo.MOTION_DETAIL_LEAVE:
            self.notify_mouse_leave()

        return False
