import { 
  Plus, 
  Printer,
  X,
  ArchiveX,
  Minus, 
  Trash2, 
  ShoppingCart, 
  Coffee, 
  Package, 
  Grid3X3, 
  ShoppingBag, 
  Utensils, 
  MoreHorizontal, 
  Pizza, 
  Cake, 
  Sandwich, 
  IceCream, 
  Cookie, 
  Soup, 
  ChevronRight, 
  CircleX, 
  CookingPot, 
  Download, 
  RefreshCw, 
  Edit, 
  Eye, 
  Lock, 
  Unlock, 
  Check, 
  CheckCircle, 
  Columns, 
  AlertTriangle, 
  Calendar, 
  MoreVertical, 
  FileText, 
  Upload, 
  FileSpreadsheet, 
  Search, 
  Filter, 
  Settings, 
  ChevronLeft, 
  Archive
} from 'lucide-vue-next'

export default {
  install(app) {
    app.component('AlertTriangle', AlertTriangle)
    app.component('Printer', Printer)
    app.component('Cake', Cake)
    app.component('ArchiveX', ArchiveX)
    app.component('Calendar', Calendar)
    app.component('Check', Check)
    app.component('CheckCircle', CheckCircle)
    app.component('ChevronLeft', ChevronLeft)
    app.component('ChevronRight', ChevronRight)
    app.component('CircleX', CircleX)
    app.component('Coffee', Coffee)
    app.component('Columns', Columns)
    app.component('Cookie', Cookie)
    app.component('CookingPot', CookingPot)
    app.component('Download', Download)
    app.component('Edit', Edit)
    app.component('Eye', Eye)
    app.component('FileSpreadsheet', FileSpreadsheet)
    app.component('FileText', FileText)
    app.component('Filter', Filter)
    app.component('Grid3X3', Grid3X3)
    app.component('IceCream', IceCream)
    app.component('Lock', Lock)
    app.component('Minus', Minus)
    app.component('MoreHorizontal', MoreHorizontal)
    app.component('MoreVertical', MoreVertical)
    app.component('Package', Package)
    app.component('Pizza', Pizza)
    app.component('Plus', Plus)
    app.component('RefreshCw', RefreshCw)
    app.component('Sandwich', Sandwich)
    app.component('Search', Search)
    app.component('Settings', Settings)
    app.component('ShoppingBag', ShoppingBag)
    app.component('ShoppingCart', ShoppingCart)
    app.component('Soup', Soup)
    app.component('ToggleLeft', ToggleLeft)
    app.component('ToggleRight', ToggleRight)
    app.component('Trash2', Trash2)
    app.component('Unlock', Unlock)
    app.component('Upload', Upload)
    app.component('Utensils', Utensils)
    app.component('X', X)
  }
}