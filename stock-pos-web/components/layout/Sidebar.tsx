'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  ShoppingCart,
  Package,
  History,
  Users,
  BarChart3,
  Megaphone,
  Settings,
  Tag,
} from 'lucide-react';

const menuItems = [
  {
    title: 'ภาพรวม',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'ขายหน้าร้าน',
    href: '/pos',
    icon: ShoppingCart,
  },
  {
    title: 'คลังสินค้า',
    href: '/inventory',
    icon: Package,
  },
  {
    title: 'ประวัติการขาย',
    href: '/history',
    icon: History,
  },
  {
    title: 'ลูกค้า',
    href: '/customers',
    icon: Users,
  },
  {
    title: 'แคมเปญ Sale',
    href: '/campaigns',
    icon: Tag,
  },
  {
    title: 'รายงาน',
    href: '/reports',
    icon: BarChart3,
  },
  {
    title: 'AI & Social',
    href: '/ai-social',
    icon: Megaphone,
  },
  {
    title: 'ตั้งค่า',
    href: '/settings',
    icon: Settings,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r bg-card h-screen sticky top-0 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b">
        <h1 className="text-2xl font-bold">Stock POS</h1>
        <p className="text-sm text-muted-foreground">ระบบ POS & สต็อก</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
                'hover:bg-accent hover:text-accent-foreground',
                isActive && 'bg-accent text-accent-foreground font-medium'
              )}
            >
              <Icon className="h-5 w-5" />
              <span>{item.title}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t text-center text-sm text-muted-foreground">
        <p>© 2026 Stock POS System</p>
      </div>
    </aside>
  );
}
